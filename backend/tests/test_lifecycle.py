"""RESERVE-X lifecycle tests.

Covers the 5 demo scenarios + risk engine correctness + edge cases.
Run with: python -m pytest backend/tests/test_lifecycle.py -v
"""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.store import store

client = TestClient(app)

API = "/api/v1"


@pytest.fixture(autouse=True)
def reset_store():
    """Clean slate before every test."""
    store.reset()
    yield
    store.reset()


# ── Helpers ──────────────────────────────────────────────────────

def _register_gpu(capacity: int = 2, name: str = "GPU Pool Alpha") -> dict:
    r = client.post(f"{API}/resources", json={
        "name": name,
        "capability": "GPU_COMPUTE",
        "total_capacity": capacity,
    })
    assert r.status_code == 201
    return r.json()


def _create_option(
    agent: str = "agent-A",
    capability: str = "GPU_COMPUTE",
    probability: float = 0.7,
    amount: int = 1,
    expires_minutes: int = 10,
) -> dict:
    r = client.post(f"{API}/options", json={
        "agent_id": agent,
        "capability": capability,
        "probability": probability,
        "amount": amount,
        "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)).isoformat(),
    })
    assert r.status_code == 201
    return r.json()


# ═════════════════════════════════════════════════════════════════
# SCENARIO 1: Prediction → option created (PENDING)
# ═════════════════════════════════════════════════════════════════

class TestScenario1_CreateOption:
    def test_create_option_returns_pending(self):
        _register_gpu()
        opt = _create_option(agent="agent-A", probability=0.7)
        assert opt["status"] == "PENDING"
        assert opt["agent_id"] == "agent-A"
        assert opt["capability"] == "GPU_COMPUTE"
        assert opt["probability"] == 0.7

    def test_create_option_logged_as_event(self):
        _register_gpu()
        opt = _create_option()
        events = client.get(f"{API}/events").json()
        # Last event before OPTION_CREATED is RESOURCE_REGISTERED
        option_events = [e for e in events if e["event_type"] == "OPTION_CREATED"]
        assert len(option_events) == 1
        assert option_events[0]["option_id"] == opt["id"]

    def test_list_options_returns_created(self):
        _register_gpu()
        _create_option(agent="agent-A")
        _create_option(agent="agent-B")
        opts = client.get(f"{API}/options").json()
        assert len(opts) == 2

    def test_list_options_filter_by_agent(self):
        _register_gpu()
        _create_option(agent="agent-A")
        _create_option(agent="agent-B")
        opts = client.get(f"{API}/options", params={"agent_id": "agent-A"}).json()
        assert len(opts) == 1
        assert opts[0]["agent_id"] == "agent-A"

    def test_list_options_filter_by_status(self):
        _register_gpu()
        _create_option(agent="agent-A")
        opts = client.get(f"{API}/options", params={"status": "EXERCISED"}).json()
        assert len(opts) == 0


# ═════════════════════════════════════════════════════════════════
# SCENARIO 2: Option exercised → actual resource allocated
# ═════════════════════════════════════════════════════════════════

class TestScenario2_ExerciseOption:
    def test_exercise_creates_allocation(self):
        gpu = _register_gpu(capacity=2)
        opt = _create_option(agent="agent-A")

        r = client.post(f"{API}/options/{opt['id']}/exercise")
        assert r.status_code == 200
        alloc = r.json()
        assert alloc["option_id"] == opt["id"]
        assert alloc["resource_id"] == gpu["id"]
        assert alloc["agent_id"] == "agent-A"
        assert alloc["amount"] == 1
        assert alloc["released_at"] is None

    def test_exercise_decrements_capacity(self):
        _register_gpu(capacity=2)
        opt = _create_option()

        client.post(f"{API}/options/{opt['id']}/exercise")

        resources = client.get(f"{API}/resources").json()
        gpu = resources[0]
        assert gpu["allocated_capacity"] == 1
        assert gpu["available_capacity"] == 1

    def test_exercise_marks_option_as_exercised(self):
        _register_gpu()
        opt = _create_option()

        client.post(f"{API}/options/{opt['id']}/exercise")

        opts = client.get(f"{API}/options", params={"status": "EXERCISED"}).json()
        assert len(opts) == 1
        assert opts[0]["id"] == opt["id"]
        assert opts[0]["exercised_at"] is not None

    def test_exercise_logs_events(self):
        _register_gpu()
        opt = _create_option()
        client.post(f"{API}/options/{opt['id']}/exercise")

        events = client.get(f"{API}/events").json()
        types = [e["event_type"] for e in events]
        assert "OPTION_EXERCISED" in types
        assert "ALLOCATION_CREATED" in types


# ═════════════════════════════════════════════════════════════════
# SCENARIO 3: Wrong prediction → expire → no waste
# ═════════════════════════════════════════════════════════════════

class TestScenario3_Expiration:
    def test_cancel_option(self):
        _register_gpu()
        opt = _create_option()

        r = client.post(f"{API}/options/{opt['id']}/cancel")
        assert r.status_code == 200
        cancelled = r.json()
        assert cancelled["status"] == "CANCELLED"
        assert cancelled["cancelled_at"] is not None

    def test_cancel_does_not_consume_resource(self):
        _register_gpu(capacity=2)
        opt = _create_option()

        client.post(f"{API}/options/{opt['id']}/cancel")

        resources = client.get(f"{API}/resources").json()
        assert resources[0]["allocated_capacity"] == 0
        assert resources[0]["available_capacity"] == 2

    def test_expired_option_via_stale_sweep(self):
        """Options with past expires_at are swept by the background task.

        We simulate this by creating an option with expires_at in the past
        and calling the engine's expire_stale_options directly.
        """
        from backend.engine.option_manager import expire_stale_options

        _register_gpu()
        # Create option that already expired
        r = client.post(f"{API}/options", json={
            "agent_id": "agent-X",
            "capability": "GPU_COMPUTE",
            "probability": 0.5,
            "expires_at": (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat(),
        })
        assert r.status_code == 201
        opt = r.json()
        assert opt["status"] == "PENDING"

        # Run sweep
        expired = expire_stale_options()
        assert len(expired) == 1
        assert expired[0].id == opt["id"]
        assert expired[0].status.value == "EXPIRED"

    def test_cancel_logs_event(self):
        _register_gpu()
        opt = _create_option()
        client.post(f"{API}/options/{opt['id']}/cancel")

        events = client.get(f"{API}/events").json()
        cancel_events = [e for e in events if e["event_type"] == "OPTION_CANCELLED"]
        assert len(cancel_events) == 1


# ═════════════════════════════════════════════════════════════════
# SCENARIO 4: Multiple options → risk/conflict detected
# ═════════════════════════════════════════════════════════════════

class TestScenario4_RiskAndConflict:
    def test_exercise_conflict_returns_409(self):
        """Capacity = 2. Exercise 2, then attempt a 3rd → 409."""
        _register_gpu(capacity=2)
        opt1 = _create_option(agent="agent-A")
        opt2 = _create_option(agent="agent-B")
        opt3 = _create_option(agent="agent-C")

        r1 = client.post(f"{API}/options/{opt1['id']}/exercise")
        assert r1.status_code == 200
        r2 = client.post(f"{API}/options/{opt2['id']}/exercise")
        assert r2.status_code == 200
        r3 = client.post(f"{API}/options/{opt3['id']}/exercise")
        assert r3.status_code == 409

    def test_exercise_failure_keeps_option_pending(self):
        _register_gpu(capacity=1)
        opt1 = _create_option(agent="agent-A")
        opt2 = _create_option(agent="agent-B")

        client.post(f"{API}/options/{opt1['id']}/exercise")
        client.post(f"{API}/options/{opt2['id']}/exercise")  # fails

        opts = client.get(f"{API}/options").json()
        opt2_state = [o for o in opts if o["id"] == opt2["id"]][0]
        assert opt2_state["status"] == "PENDING"  # stays PENDING, not lost

    def test_exercise_failure_logs_event(self):
        _register_gpu(capacity=1)
        opt1 = _create_option(agent="agent-A")
        opt2 = _create_option(agent="agent-B")

        client.post(f"{API}/options/{opt1['id']}/exercise")
        client.post(f"{API}/options/{opt2['id']}/exercise")

        events = client.get(f"{API}/events").json()
        fail_events = [e for e in events if e["event_type"] == "EXERCISE_FAILED"]
        assert len(fail_events) == 1
        assert fail_events[0]["details"]["reason"] == "insufficient_capacity"

    def test_risk_detects_overcommitment(self):
        """Capacity=2, three options at 80%/70%/60% → non-trivial overcommit risk."""
        _register_gpu(capacity=2)
        _create_option(agent="agent-A", probability=0.8)
        _create_option(agent="agent-B", probability=0.7)
        _create_option(agent="agent-C", probability=0.6)

        risk = client.get(f"{API}/risk").json()
        gpu_risk = risk["capability_risks"][0]
        assert gpu_risk["capability"] == "GPU_COMPUTE"
        assert gpu_risk["pending_options_count"] == 3

        # P(all 3 exercise) = 0.8 * 0.7 * 0.6 = 0.336
        # That's the only subset exceeding capacity=2
        assert abs(gpu_risk["overcommit_probability"] - 0.336) < 0.001
        assert gpu_risk["risk_level"] == "HIGH"

    def test_risk_low_with_ample_capacity(self):
        """Capacity=10, one option at 50% → LOW risk."""
        _register_gpu(capacity=10)
        _create_option(probability=0.5)

        risk = client.get(f"{API}/risk").json()
        gpu_risk = risk["capability_risks"][0]
        assert gpu_risk["overcommit_probability"] == 0.0
        assert gpu_risk["risk_level"] == "LOW"

    def test_risk_with_no_pending_options(self):
        _register_gpu(capacity=2)
        risk = client.get(f"{API}/risk").json()
        gpu_risk = risk["capability_risks"][0]
        assert gpu_risk["overcommit_probability"] == 0.0
        assert gpu_risk["risk_level"] == "LOW"


# ═════════════════════════════════════════════════════════════════
# SCENARIO 5: Agent cancels future need
# ═════════════════════════════════════════════════════════════════

class TestScenario5_Cancel:
    def test_cancel_reduces_risk(self):
        _register_gpu(capacity=1)
        opt1 = _create_option(agent="agent-A", probability=0.9)
        opt2 = _create_option(agent="agent-B", probability=0.8)

        # Risk before cancel
        risk_before = client.get(f"{API}/risk").json()
        p_before = risk_before["capability_risks"][0]["overcommit_probability"]

        # Cancel one option
        client.post(f"{API}/options/{opt2['id']}/cancel")

        # Risk after cancel
        risk_after = client.get(f"{API}/risk").json()
        p_after = risk_after["capability_risks"][0]["overcommit_probability"]

        assert p_after < p_before
        assert p_after == 0.0  # 1 option, capacity=1, can't overcommit

    def test_cannot_cancel_exercised_option(self):
        _register_gpu()
        opt = _create_option()
        client.post(f"{API}/options/{opt['id']}/exercise")
        r = client.post(f"{API}/options/{opt['id']}/cancel")
        assert r.status_code == 409

    def test_cannot_exercise_cancelled_option(self):
        _register_gpu()
        opt = _create_option()
        client.post(f"{API}/options/{opt['id']}/cancel")
        r = client.post(f"{API}/options/{opt['id']}/exercise")
        assert r.status_code == 409


# ═════════════════════════════════════════════════════════════════
# Probability update → risk recalculation
# ═════════════════════════════════════════════════════════════════

class TestProbabilityUpdate:
    def test_update_probability(self):
        _register_gpu()
        opt = _create_option(probability=0.7)

        r = client.patch(f"{API}/options/{opt['id']}", json={"probability": 0.3})
        assert r.status_code == 200
        updated = r.json()
        assert updated["probability"] == 0.3

    def test_update_probability_changes_risk(self):
        _register_gpu(capacity=1)
        opt1 = _create_option(agent="agent-A", probability=0.9)
        opt2 = _create_option(agent="agent-B", probability=0.9)

        risk_high = client.get(f"{API}/risk").json()
        p_high = risk_high["capability_risks"][0]["overcommit_probability"]

        # Agent B lowers confidence
        client.patch(f"{API}/options/{opt2['id']}", json={"probability": 0.1})

        risk_low = client.get(f"{API}/risk").json()
        p_low = risk_low["capability_risks"][0]["overcommit_probability"]

        assert p_low < p_high

    def test_update_logs_event(self):
        _register_gpu()
        opt = _create_option(probability=0.7)
        client.patch(f"{API}/options/{opt['id']}", json={"probability": 0.3})

        events = client.get(f"{API}/events").json()
        update_events = [e for e in events if e["event_type"] == "OPTION_UPDATED"]
        assert len(update_events) == 1
        assert update_events[0]["details"]["old_probability"] == 0.7
        assert update_events[0]["details"]["new_probability"] == 0.3

    def test_cannot_update_exercised_option(self):
        _register_gpu()
        opt = _create_option()
        client.post(f"{API}/options/{opt['id']}/exercise")
        r = client.patch(f"{API}/options/{opt['id']}", json={"probability": 0.1})
        assert r.status_code == 409


# ═════════════════════════════════════════════════════════════════
# Allocation release
# ═════════════════════════════════════════════════════════════════

class TestAllocationRelease:
    def test_release_frees_capacity(self):
        _register_gpu(capacity=2)
        opt = _create_option()
        alloc = client.post(f"{API}/options/{opt['id']}/exercise").json()

        # Capacity should be 1 available
        resources = client.get(f"{API}/resources").json()
        assert resources[0]["available_capacity"] == 1

        # Release
        r = client.post(f"{API}/allocations/{alloc['id']}/release")
        assert r.status_code == 200
        released = r.json()
        assert released["released_at"] is not None

        # Capacity should be 2 again
        resources = client.get(f"{API}/resources").json()
        assert resources[0]["available_capacity"] == 2

    def test_double_release_returns_409(self):
        _register_gpu()
        opt = _create_option()
        alloc = client.post(f"{API}/options/{opt['id']}/exercise").json()
        client.post(f"{API}/allocations/{alloc['id']}/release")
        r = client.post(f"{API}/allocations/{alloc['id']}/release")
        assert r.status_code == 409


# ═════════════════════════════════════════════════════════════════
# Risk engine unit tests
# ═════════════════════════════════════════════════════════════════

class TestRiskEngine:
    def test_single_option_below_capacity(self):
        """1 option, amount=1, capacity=1 → P(overcommit)=0."""
        _register_gpu(capacity=1)
        _create_option(probability=0.9)
        risk = client.get(f"{API}/risk").json()
        assert risk["capability_risks"][0]["overcommit_probability"] == 0.0

    def test_two_options_capacity_one(self):
        """2 options (p=0.5, p=0.5), capacity=1 → P(both)=0.25."""
        _register_gpu(capacity=1)
        _create_option(agent="A", probability=0.5)
        _create_option(agent="B", probability=0.5)
        risk = client.get(f"{API}/risk").json()
        assert abs(risk["capability_risks"][0]["overcommit_probability"] - 0.25) < 0.001

    def test_expected_demand(self):
        """E[demand] = sum(p_i * a_i)."""
        _register_gpu(capacity=10)
        _create_option(agent="A", probability=0.8)
        _create_option(agent="B", probability=0.6)
        risk = client.get(f"{API}/risk").json()
        # E = 0.8*1 + 0.6*1 = 1.4
        assert abs(risk["capability_risks"][0]["expected_demand"] - 1.4) < 0.01

    def test_system_risk_highest_level(self):
        """Highest risk level across capabilities is reported."""
        _register_gpu(capacity=1)
        # Register a second resource type
        client.post(f"{API}/resources", json={
            "name": "Code Runner",
            "capability": "CODE_EXECUTION",
            "total_capacity": 10,
        })
        # GPU: 2 options, cap=1 → HIGH risk
        _create_option(agent="A", probability=0.8)
        _create_option(agent="B", probability=0.7)
        # CODE_EXECUTION: no options → LOW risk

        risk = client.get(f"{API}/risk").json()
        assert risk["highest_risk_level"] in ("HIGH", "CRITICAL", "MEDIUM")


# ═════════════════════════════════════════════════════════════════
# Status endpoint
# ═════════════════════════════════════════════════════════════════

class TestStatusEndpoint:
    def test_status_returns_full_snapshot(self):
        _register_gpu()
        _create_option()
        status = client.get(f"{API}/status").json()
        assert "resources" in status
        assert "options" in status
        assert "allocations" in status
        assert "risk" in status
        assert len(status["resources"]) == 1
        assert len(status["options"]) == 1


# ═════════════════════════════════════════════════════════════════
# Edge cases
# ═════════════════════════════════════════════════════════════════

class TestEdgeCases:
    def test_exercise_nonexistent_option(self):
        r = client.post(f"{API}/options/nonexistent/exercise")
        assert r.status_code == 404

    def test_cancel_nonexistent_option(self):
        r = client.post(f"{API}/options/nonexistent/cancel")
        assert r.status_code == 404

    def test_release_nonexistent_allocation(self):
        r = client.post(f"{API}/allocations/nonexistent/release")
        assert r.status_code == 404

    def test_exercise_without_any_resources(self):
        """Option exists but no resources are registered for its capability."""
        opt = _create_option()
        r = client.post(f"{API}/options/{opt['id']}/exercise")
        assert r.status_code == 409

    def test_root_endpoint(self):
        r = client.get("/")
        assert r.status_code == 200
        assert r.json()["name"] == "RESERVE-X"
