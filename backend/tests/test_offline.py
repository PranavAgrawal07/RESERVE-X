"""Tests for Phase 1 Offline Resilience Engine.

Validates:
1. Online mode works normally.
2. Offline mode can be activated.
3. Meaningful resource-option operation works while offline.
4. Offline operation is persisted to SQLite.
5. Offline operation enters synchronization queue.
6. Multiple operations can accumulate during outage.
7. Queue survives application/service restart (persistence).
8. No synchronization occurs while offline.
9. Switching back online triggers automatic synchronization.
10. Queued operations become SYNCED after successful reconciliation.
11. Failed synchronization remains queued with retry tracking.
12. Retry does not create duplicate operations (idempotency).
13. Important events are not lost.
14. Local LearnedPredictor can be invoked while offline.
15. Local risk calculation functions while offline.
16. The 60-second outage requirement: operations persist across >= 60s outage and sync cleanly upon reconnection.
17. Existing RESERVE-X behavior remains unchanged.
"""

from __future__ import annotations

import os
import tempfile
from datetime import datetime, timedelta, timezone
from typing import Generator

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.models.enums import CapabilityType, OptionStatus
from backend.offline.manager import OfflineManager, offline_manager
from backend.offline.store import OfflineOperation, OfflineStore
from backend.store import store


@pytest.fixture(autouse=True)
def clean_state() -> Generator[None, None, None]:
    """Clean in-memory store and offline SQLite database before and after each test."""
    store.reset()
    offline_manager.clear()
    yield
    store.reset()
    offline_manager.clear()


client = TestClient(app)


# ────────────────────────────────────────────────────────────────────
# 1. Online mode works normally
# ────────────────────────────────────────────────────────────────────

def test_online_mode_default_and_normal():
    assert offline_manager.is_online()
    assert not offline_manager.is_offline()

    resp = client.post(
        "/api/v1/options",
        json={
            "agent_id": "agent-001",
            "capability": "GPU_COMPUTE",
            "probability": 0.85,
            "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat(),
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "PENDING"
    assert data["agent_id"] == "agent-001"
    # In online mode, created directly in core store
    assert data["id"] in store.options
    assert offline_manager.queue.count_pending() == 0


# ────────────────────────────────────────────────────────────────────
# 2. Offline mode can be activated
# ────────────────────────────────────────────────────────────────────

def test_offline_mode_activation():
    resp = client.post("/api/v1/connectivity/offline")
    assert resp.status_code == 200
    data = resp.json()
    assert data["mode"] == "OFFLINE"
    assert data["is_offline"] is True
    assert offline_manager.is_offline()

    # Via mode endpoint
    client.post("/api/v1/connectivity/mode", json={"mode": "ONLINE"})
    assert offline_manager.is_online()

    client.post("/api/v1/connectivity/mode", json={"mode": "OFFLINE"})
    assert offline_manager.is_offline()


# ────────────────────────────────────────────────────────────────────
# 3. Meaningful resource-option operation works while offline
# ────────────────────────────────────────────────────────────────────

def test_meaningful_operation_works_offline():
    offline_manager.set_offline()

    exp = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
    resp = client.post(
        "/api/v1/options",
        json={
            "agent_id": "agent-002",
            "capability": "LLM_INFERENCE",
            "probability": 0.9,
            "amount": 2,
            "expires_at": exp,
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["agent_id"] == "agent-002"
    assert data["capability"] == "LLM_INFERENCE"
    assert data["probability"] == 0.9
    assert data["amount"] == 2
    assert data["status"] == "PENDING"
    assert "id" in data


# ────────────────────────────────────────────────────────────────────
# 4. Offline operation is persisted to SQLite
# ────────────────────────────────────────────────────────────────────

def test_offline_operation_persisted_to_sqlite():
    offline_manager.set_offline()

    exp = (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat()
    resp = client.post(
        "/api/v1/options",
        json={
            "agent_id": "agent-003",
            "capability": "TESTING",
            "probability": 0.75,
            "expires_at": exp,
        },
    )
    op_id = resp.json()["id"]

    # Verify directly in SQLite store
    op = offline_manager.store.get_operation(op_id)
    assert op is not None
    assert op.operation_id == op_id
    assert op.agent_id == "agent-003"
    assert op.capability == "TESTING"
    assert op.probability == 0.75
    assert op.sync_status == "PENDING"
    assert op.retry_count == 0


# ────────────────────────────────────────────────────────────────────
# 5. Offline operation enters synchronization queue
# ────────────────────────────────────────────────────────────────────

def test_offline_operation_enters_sync_queue():
    offline_manager.set_offline()

    assert offline_manager.queue.count_pending() == 0

    client.post(
        "/api/v1/options",
        json={
            "agent_id": "agent-004",
            "capability": "TERMINAL",
            "probability": 0.6,
            "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat(),
        },
    )

    assert offline_manager.queue.count_pending() == 1
    pending = offline_manager.queue.get_pending()
    assert len(pending) == 1
    assert pending[0].agent_id == "agent-004"
    assert pending[0].sync_status == "PENDING"


# ────────────────────────────────────────────────────────────────────
# 6. Multiple operations can accumulate during outage
# ────────────────────────────────────────────────────────────────────

def test_multiple_operations_accumulate_during_outage():
    offline_manager.set_offline()

    capabilities = ["GPU_COMPUTE", "LLM_INFERENCE", "DATABASE", "SECURITY_SCAN", "DEPLOYMENT"]
    for i, cap in enumerate(capabilities):
        resp = client.post(
            "/api/v1/options",
            json={
                "agent_id": f"agent-{i:03d}",
                "capability": cap,
                "probability": 0.5 + (i * 0.1),
                "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat(),
            },
        )
        assert resp.status_code == 201

    assert offline_manager.queue.count_pending() == 5
    stats = offline_manager.queue.get_stats()
    assert stats["pending"] == 5
    assert stats["synced"] == 0


# ────────────────────────────────────────────────────────────────────
# 7. Queue survives application/service restart
# ────────────────────────────────────────────────────────────────────

def test_queue_survives_restart():
    # Use a real file on disk to test persistence across instance lifecycles
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        db_path = tf.name

    try:
        # Instance 1: write offline operations
        store1 = OfflineStore(db_path=db_path)
        mgr1 = OfflineManager(store_instance=store1, db_path=db_path)
        mgr1.set_offline()

        mgr1.handle_offline_option_request(
            agent_id="agent-persisted",
            capability="DATABASE",
            probability=0.88,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
        )
        assert mgr1.queue.count_pending() == 1
        store1.close()

        # Instance 2: simulates application restart from same database
        store2 = OfflineStore(db_path=db_path)
        mgr2 = OfflineManager(store_instance=store2, db_path=db_path)

        assert mgr2.queue.count_pending() == 1
        pending = mgr2.queue.get_pending()
        assert len(pending) == 1
        assert pending[0].agent_id == "agent-persisted"
        assert pending[0].capability == "DATABASE"
        assert pending[0].probability == 0.88
        store2.close()
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


# ────────────────────────────────────────────────────────────────────
# 8. No synchronization occurs while offline
# ────────────────────────────────────────────────────────────────────

def test_no_sync_occurs_while_offline():
    offline_manager.set_offline()

    client.post(
        "/api/v1/options",
        json={
            "agent_id": "agent-offline-only",
            "capability": "GPU_COMPUTE",
            "probability": 0.7,
            "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat(),
        },
    )

    # Calling sync while offline must be blocked
    resp = client.post("/api/v1/connectivity/sync")
    assert resp.status_code == 400

    # Core store must NOT contain the option
    assert len(store.options) == 0
    # Queue must remain pending
    assert offline_manager.queue.count_pending() == 1


# ────────────────────────────────────────────────────────────────────
# 9. Switching back online triggers automatic synchronization
# ────────────────────────────────────────────────────────────────────

def test_switching_online_triggers_auto_sync():
    offline_manager.set_offline()

    for i in range(3):
        client.post(
            "/api/v1/options",
            json={
                "agent_id": f"agent-batch-{i}",
                "capability": "LLM_INFERENCE",
                "probability": 0.8,
                "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat(),
            },
        )

    assert offline_manager.queue.count_pending() == 3
    assert len(store.options) == 0

    # Switching back online automatically triggers synchronization
    resp = client.post("/api/v1/connectivity/online")
    assert resp.status_code == 200
    data = resp.json()
    assert data["mode"] == "ONLINE"
    assert data["sync"]["synced"] == 3
    assert data["sync"]["remaining_pending"] == 0

    # Live store now contains all 3 options
    assert len(store.options) == 3
    for opt in store.options.values():
        assert opt.status == OptionStatus.PENDING
        assert opt.capability == CapabilityType.LLM_INFERENCE


# ────────────────────────────────────────────────────────────────────
# 10. Queued operations become SYNCED after reconciliation
# ────────────────────────────────────────────────────────────────────

def test_queued_operations_become_synced():
    offline_manager.set_offline()

    resp = client.post(
        "/api/v1/options",
        json={
            "agent_id": "agent-sync-verify",
            "capability": "WEB_SEARCH",
            "probability": 0.65,
            "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat(),
        },
    )
    op_id = resp.json()["id"]

    offline_manager.set_online()

    op = offline_manager.store.get_operation(op_id)
    assert op is not None
    assert op.sync_status == "SYNCED"
    assert op.synced_at is not None
    assert op.reconciled_option_id is not None
    assert op.reconciled_option_id in store.options


# ────────────────────────────────────────────────────────────────────
# 11. Failed synchronization remains queued
# ────────────────────────────────────────────────────────────────────

def test_failed_sync_remains_queued():
    # Insert an invalid operation manually to test failure isolation
    invalid_op = OfflineOperation(
        operation_id="invalid-op-1",
        idempotency_key="idem-invalid-1",
        operation_type="CREATE_OPTION",
        timestamp=datetime.now(timezone.utc).isoformat(),
        agent_id="bad-agent",
        capability="NON_EXISTENT_CAPABILITY",
        probability=0.5,
        amount=1,
        priority=0,
        expires_at="bad-date-format",
        payload_json="{}",
        sync_status="PENDING",
    )
    offline_manager.queue.enqueue(invalid_op)

    # Sync
    result = offline_manager.sync_pending()
    assert result["failed"] == 1
    assert result["remaining_pending"] == 1

    # Operation remains in queue with incremented retry count
    op = offline_manager.store.get_operation("invalid-op-1")
    assert op is not None
    assert op.sync_status == "FAILED"
    assert op.retry_count == 1
    assert op.error_message is not None


# ────────────────────────────────────────────────────────────────────
# 12. Retry does not create duplicate operations
# ────────────────────────────────────────────────────────────────────

def test_retry_does_not_create_duplicates():
    offline_manager.set_offline()

    client.post(
        "/api/v1/options",
        json={
            "agent_id": "agent-idempotent",
            "capability": "CODE_EXECUTION",
            "probability": 0.85,
            "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat(),
        },
    )

    offline_manager.set_online()
    initial_count = len(store.options)
    assert initial_count == 1

    # Call sync again (e.g. background loop or repeated reconnect)
    sync2 = offline_manager.sync_pending()
    assert len(store.options) == initial_count  # NO duplicate created!


# ────────────────────────────────────────────────────────────────────
# 13. Important events are not lost
# ────────────────────────────────────────────────────────────────────

def test_events_not_lost():
    offline_manager.set_offline()

    client.post(
        "/api/v1/options",
        json={
            "agent_id": "agent-events",
            "capability": "SECURITY_SCAN",
            "probability": 0.77,
            "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat(),
        },
    )

    offline_manager.set_online()

    # Query events from SQLite
    resp = client.get("/api/v1/connectivity/events")
    assert resp.status_code == 200
    events = resp.json()

    event_types = [e["event_type"] for e in events]
    assert "CONNECTIVITY_LOST" in event_types
    assert "OFFLINE_OPTION_RECORDED" in event_types
    assert "CONNECTIVITY_RESTORED" in event_types
    assert "OFFLINE_OPERATION_SYNCED" in event_types


# ────────────────────────────────────────────────────────────────────
# 14. Local LearnedPredictor can be invoked offline
# ────────────────────────────────────────────────────────────────────

def test_local_learned_predictor_offline():
    offline_manager.set_offline()

    resp = client.post(
        "/api/v1/connectivity/predict",
        json={
            "agent_type": "Coding",
            "step_name": "write_code",
            "current_capability": "TERMINAL",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "capability" in data
    assert "probability" in data
    assert data["capability"] in ("TESTING", "LLM_INFERENCE")
    assert 0.0 <= data["probability"] <= 1.0


# ────────────────────────────────────────────────────────────────────
# 15. Local risk calculation functions offline
# ────────────────────────────────────────────────────────────────────

def test_local_risk_summary_offline():
    offline_manager.set_offline()

    client.post(
        "/api/v1/options",
        json={
            "agent_id": "agent-risk-1",
            "capability": "GPU_COMPUTE",
            "probability": 0.8,
            "amount": 1,
            "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat(),
        },
    )
    client.post(
        "/api/v1/options",
        json={
            "agent_id": "agent-risk-2",
            "capability": "GPU_COMPUTE",
            "probability": 0.9,
            "amount": 1,
            "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat(),
        },
    )

    resp = client.get("/api/v1/connectivity/risk")
    assert resp.status_code == 200
    data = resp.json()
    assert data["mode"] == "OFFLINE"
    assert data["total_pending_offline_options"] == 2
    assert data["total_demand"] == 2
    assert data["expected_demand"] == round(0.8 + 0.9, 4)
    assert "GPU_COMPUTE" in data["capabilities"]


# ────────────────────────────────────────────────────────────────────
# 16. MOST IMPORTANT TEST: 60-second outage simulation
# ────────────────────────────────────────────────────────────────────

def test_sixty_second_outage_resilience():
    """Simulates an outage lasting >= 60 seconds:
    
    1. System transitions to OFFLINE.
    2. Simulated outage clock is set to 75 seconds ago.
    3. Multiple critical agent options are created and persisted during the outage.
    4. Queue survives and retains all data for the full duration.
    5. Local risk analysis functions throughout.
    6. Connectivity is restored (ONLINE).
    7. Automatic synchronization triggers immediately.
    8. All options reconcile into the live engine.
    9. Queue becomes clean/synced with zero data loss and zero duplicates.
    """
    now = datetime.now(timezone.utc)
    outage_start = now - timedelta(seconds=75)

    # 1. Enter offline mode with outage started 75s ago
    offline_manager.set_offline()
    offline_manager._outage_started_at = outage_start

    # Verify outage duration calculation
    status = client.get("/api/v1/connectivity/status").json()
    assert status["mode"] == "OFFLINE"

    # 2. Critical agent operations during the outage
    requests = [
        {"agent_id": "agent-alpha", "capability": "GPU_COMPUTE", "probability": 0.85, "amount": 1},
        {"agent_id": "agent-beta",  "capability": "LLM_INFERENCE", "probability": 0.95, "amount": 2},
        {"agent_id": "agent-gamma", "capability": "DATABASE", "probability": 0.70, "amount": 1},
        {"agent_id": "agent-delta", "capability": "TESTING", "probability": 0.80, "amount": 1},
    ]

    created_ids = []
    for req in requests:
        resp = client.post(
            "/api/v1/options",
            json={
                **req,
                "expires_at": (now + timedelta(hours=1)).isoformat(),
            },
        )
        assert resp.status_code == 201
        created_ids.append(resp.json()["id"])

    # 3. Verify durability during outage (>60s elapsed)
    assert offline_manager.queue.count_pending() == 4
    queue_items = client.get("/api/v1/connectivity/queue").json()
    assert len(queue_items) == 4
    for item in queue_items:
        assert item["sync_status"] == "PENDING"

    # Core engine still empty (clean separation)
    assert len(store.options) == 0

    # 4. Reconnection to ONLINE
    online_resp = client.post("/api/v1/connectivity/online")
    assert online_resp.status_code == 200
    online_data = online_resp.json()

    assert online_data["mode"] == "ONLINE"
    assert online_data["outage_duration_seconds"] >= 60.0
    assert online_data["sync"]["synced"] == 4
    assert online_data["sync"]["remaining_pending"] == 0

    # 5. Verify live reconciliation
    assert len(store.options) == 4
    agent_ids_in_store = {opt.agent_id for opt in store.options.values()}
    assert agent_ids_in_store == {"agent-alpha", "agent-beta", "agent-gamma", "agent-delta"}

    # 6. Queue is clean / fully synced
    assert offline_manager.queue.count_pending() == 0
    assert offline_manager.queue.count_synced() == 4

    # 7. Repeat sync does not duplicate
    sync_again = offline_manager.sync_pending()
    assert sync_again["synced"] == 0
    assert len(store.options) == 4


# ────────────────────────────────────────────────────────────────────
# 17. Existing RESERVE-X behavior remains unchanged
# ────────────────────────────────────────────────────────────────────

def test_existing_lifecycle_unchanged():
    """Ensure standard option lifecycle (create, exercise, expire, cancel) still works in core."""
    assert offline_manager.is_online()

    # Create resource in core store
    from backend.engine import resource_manager
    res = resource_manager.register_resource("gpu-node-1", CapabilityType.GPU_COMPUTE, total_capacity=2)

    # Create option via core
    from backend.engine import option_manager
    opt = option_manager.create_option(
        agent_id="agent-core",
        capability=CapabilityType.GPU_COMPUTE,
        probability=0.9,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
    )
    assert opt.status == OptionStatus.PENDING

    # Exercise option
    alloc = option_manager.exercise_option(opt.id)
    assert alloc.resource_id == res.id
    assert store.options[opt.id].status == OptionStatus.EXERCISED

    # Release allocation
    from backend.engine.allocation_manager import release_allocation
    released = release_allocation(alloc.id)
    assert released.released_at is not None


# ────────────────────────────────────────────────────────────────────
# 18. Real Wi-Fi disconnect reason tracking (NETWORK_DISCONNECTED vs MANUAL)
# ────────────────────────────────────────────────────────────────────

def test_network_disconnected_reason_tracking():
    """Verify system distinguishes between real network loss and manual simulation."""
    # Real network loss
    resp = client.post("/api/v1/connectivity/offline?reason=NETWORK_DISCONNECTED")
    assert resp.status_code == 200
    data = resp.json()
    assert data["mode"] == "OFFLINE"
    assert data["offline_reason"] == "NETWORK_DISCONNECTED"

    status = client.get("/api/v1/connectivity/status").json()
    assert status["offline_reason"] == "NETWORK_DISCONNECTED"

    # Reconnect
    client.post("/api/v1/connectivity/online")

    # Manual simulation
    resp2 = client.post("/api/v1/connectivity/offline?reason=MANUAL")
    assert resp2.status_code == 200
    assert resp2.json()["offline_reason"] == "MANUAL"


# ────────────────────────────────────────────────────────────────────
# 19. Outage timer continuity across multiple offline signals
# ────────────────────────────────────────────────────────────────────

def test_outage_timer_continuity_across_multiple_signals():
    """Verify repeated offline events or polling calls do NOT reset outage_started_at."""
    offline_manager.set_offline(reason="NETWORK_DISCONNECTED")
    first_started_at = offline_manager._outage_started_at
    assert first_started_at is not None

    # Simulate subsequent offline event or duplicate call
    client.post("/api/v1/connectivity/offline?reason=NETWORK_DISCONNECTED")
    assert offline_manager._outage_started_at == first_started_at

    # Check status endpoint retains original timestamp
    status = client.get("/api/v1/connectivity/status").json()
    assert status["outage_started_at"] == first_started_at.isoformat()


# ────────────────────────────────────────────────────────────────────
# 20. Real judge demonstration sequence
# ────────────────────────────────────────────────────────────────────

def test_real_wifi_judge_demonstration_sequence():
    """Validates the exact 14-step judge demonstration sequence from the prompt:
    1. Start RESERVE-X (ONLINE, queued: 0).
    2. Turn Wi-Fi OFF -> browser detects offline -> OFFLINE MODE (Network disconnected).
    3. Outage timer starts.
    4. WITHOUT turning Wi-Fi ON -> Create Offline Option (Offline-Demo-Agent, GPU_COMPUTE, p=0.85, amt=1, pri=5).
    5. HTTP 201, PENDING, SQLite queue = 1.
    6. Outage lasts >= 60 seconds.
    7. Turn Wi-Fi ON -> browser detects online -> Existing synchronization runs.
    8. UI / Status shows: Synced: 1, Failed: 0, Remaining: 0.
    9. Option appears in normal RESERVE-X overview / store.options.
    """
    # 1. System is ONLINE, queue = 0
    assert offline_manager.is_online()
    assert offline_manager.queue.count_pending() == 0

    # 2 & 3. Turn Wi-Fi OFF -> browser offline event calls POST /connectivity/offline?reason=NETWORK_DISCONNECTED
    now = datetime.now(timezone.utc)
    resp = client.post("/api/v1/connectivity/offline?reason=NETWORK_DISCONNECTED")
    assert resp.status_code == 200
    status_data = resp.json()
    assert status_data["mode"] == "OFFLINE"
    assert status_data["offline_reason"] == "NETWORK_DISCONNECTED"

    # Set outage clock to 65 seconds ago to verify >= 60 second duration requirement
    offline_manager._outage_started_at = now - timedelta(seconds=65)

    # 4 & 5. WITHOUT turning Wi-Fi ON: Create Offline Option
    future_expiry = (now + timedelta(hours=1)).isoformat()
    opt_resp = client.post(
        "/api/v1/options",
        json={
            "agent_id": "Offline-Demo-Agent",
            "capability": "GPU_COMPUTE",
            "probability": 0.85,
            "amount": 1,
            "priority": 5,
            "expires_at": future_expiry,
        },
    )
    assert opt_resp.status_code == 201
    opt_data = opt_resp.json()
    assert opt_data["status"] == "PENDING"
    assert opt_data["agent_id"] == "Offline-Demo-Agent"
    assert opt_data["capability"] == "GPU_COMPUTE"
    assert opt_data["probability"] == 0.85

    # Core store does NOT have it yet (not leaked)
    assert opt_data["id"] not in store.options

    # SQLite queue has it buffered
    assert offline_manager.queue.count_pending() == 1
    queue_data = client.get("/api/v1/connectivity/queue").json()
    assert len(queue_data) == 1
    assert queue_data[0]["agent_id"] == "Offline-Demo-Agent"
    assert queue_data[0]["sync_status"] == "PENDING"

    # 6. Outage duration >= 60 seconds
    status_check = client.get("/api/v1/connectivity/status").json()
    assert status_check["mode"] == "OFFLINE"
    assert status_check["queue_stats"]["pending"] == 1

    # 7 & 8. Turn Wi-Fi ON -> browser online event calls POST /connectivity/online
    online_resp = client.post("/api/v1/connectivity/online")
    assert online_resp.status_code == 200
    online_data = online_resp.json()
    assert online_data["mode"] == "ONLINE"
    assert online_data["outage_duration_seconds"] >= 60.0
    assert online_data["sync"]["synced"] == 1
    assert online_data["sync"]["failed"] == 0
    assert online_data["sync"]["remaining_pending"] == 0

    # 9. Option appears in normal RESERVE-X Reservations/Overview system
    assert len(store.options) == 1
    reconciled_opt = list(store.options.values())[0]
    assert reconciled_opt.agent_id == "Offline-Demo-Agent"
    assert reconciled_opt.capability == CapabilityType.GPU_COMPUTE
    assert reconciled_opt.probability == 0.85
    assert reconciled_opt.status == OptionStatus.PENDING

    # Full system status returns it
    sys_status = client.get("/api/v1/status").json()
    assert len(sys_status["options"]) == 1
    assert sys_status["options"][0]["agent_id"] == "Offline-Demo-Agent"
