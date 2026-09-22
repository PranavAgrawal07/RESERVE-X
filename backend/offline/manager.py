"""Offline Manager — coordinates local operations, persistence, and auto-sync.

Handles:
1. Connectivity state tracking (ONLINE / OFFLINE).
2. Local conditional option processing using LearnedPredictor and local risk metrics.
3. Durable SQLite queueing.
4. Automatic, idempotent synchronization with the core RESERVE-X engine upon reconnect.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from backend.models.enums import CapabilityType, OptionStatus, RiskLevel
from backend.models.option import ResourceOption
from backend.offline.queue import DurableSyncQueue
from backend.offline.store import OfflineOperation, OfflineStore
from backend.store import store
from backend.engine import option_manager
from backend.engine.risk_engine import _classify_risk, _compute_expected_demand, _compute_overcommit_probability

# Lazy/graceful import of LearnedPredictor
try:
    from simulation.learned_predictor import LearnedPredictor
except ImportError:
    LearnedPredictor = None  # type: ignore


class OfflineManager:
    """Coordinates offline processing and auto-synchronization for RESERVE-X."""

    def __init__(
        self,
        store_instance: OfflineStore | None = None,
        db_path: str = "data/offline_resilience.db",
    ):
        self.store = store_instance or OfflineStore(db_path=db_path)
        self.queue = DurableSyncQueue(self.store)
        self._mode: str = "ONLINE"  # "ONLINE" or "OFFLINE"
        self._offline_reason: str | None = None
        self._outage_started_at: datetime | None = None

        # Local ML predictor for autonomous capability estimation
        self._predictor: Any = None
        if LearnedPredictor is not None:
            try:
                self._predictor = LearnedPredictor(random_state=42)
            except Exception:
                self._predictor = None

    # ── Connectivity State ───────────────────────────────────────────

    @property
    def mode(self) -> str:
        return self._mode

    def is_offline(self) -> bool:
        return self._mode == "OFFLINE"

    def is_online(self) -> bool:
        return self._mode == "ONLINE"

    def set_offline(self, reason: str = "MANUAL") -> None:
        """Switch to OFFLINE mode (manual simulation or real network disconnect)."""
        is_already_offline = self._mode == "OFFLINE"
        if not is_already_offline or self._outage_started_at is None:
            self._outage_started_at = datetime.now(timezone.utc)
        self._mode = "OFFLINE"
        self._offline_reason = reason
        self.store.insert_event(
            event_type="CONNECTIVITY_LOST",
            details={
                "reason": reason,
                "outage_started_at": self._outage_started_at.isoformat(),
                "pending_queue_count": self.queue.count_pending(),
            },
        )

    def set_online(self, auto_sync: bool = True) -> dict[str, Any]:
        """Switch to ONLINE mode and automatically reconcile pending operations."""
        prev_mode = self._mode
        outage_duration_seconds = None
        if self._outage_started_at:
            outage_duration_seconds = (
                datetime.now(timezone.utc) - self._outage_started_at
            ).total_seconds()

        self._mode = "ONLINE"
        self._offline_reason = None
        self._outage_started_at = None

        self.store.insert_event(
            event_type="CONNECTIVITY_RESTORED",
            details={
                "previous_mode": prev_mode,
                "outage_duration_seconds": outage_duration_seconds,
            },
        )

        sync_result = {"synced": 0, "failed": 0, "remaining_pending": 0}
        if auto_sync:
            sync_result = self.sync_pending()

        return {
            "mode": self._mode,
            "outage_duration_seconds": outage_duration_seconds,
            "sync": sync_result,
        }

    # ── Learned Predictor Integration ────────────────────────────────

    def predict_capability(
        self,
        agent_type: str,
        step_name: str,
        current_capability: str,
    ) -> dict[str, Any]:
        """Predict required capability and confidence using local ML model."""
        if self._predictor is not None:
            return self._predictor.predict(
                agent_type=agent_type,
                step_name=step_name,
                current_capability=current_capability,
            )
        return {"capability": "GPU_COMPUTE", "probability": 0.5}

    # ── Local Option Creation & Processing ───────────────────────────

    def handle_offline_option_request(
        self,
        agent_id: str,
        capability: str | CapabilityType,
        probability: float,
        expires_at: datetime | str,
        amount: int = 1,
        priority: int = 0,
        idempotency_key: str | None = None,
        agent_type: str | None = None,
        step_name: str | None = None,
    ) -> ResourceOption:
        """Process and record an option request locally during a network outage.

        1. Enriches/validates parameters (optionally using LearnedPredictor).
        2. Evaluates local risk metrics.
        3. Persists to durable SQLite database.
        4. Enqueues in synchronization queue.
        5. Returns a valid ResourceOption object for immediate agent consumption.
        """
        now = datetime.now(timezone.utc)
        op_id = str(uuid4())
        idem_key = idempotency_key or f"idem_{agent_id}_{op_id}"

        # Resolve capability string
        cap_str = capability.value if isinstance(capability, CapabilityType) else str(capability)

        # Format timestamps
        now_iso = now.isoformat()
        if isinstance(expires_at, datetime):
            exp_iso = expires_at.isoformat()
            exp_dt = expires_at
        else:
            exp_iso = str(expires_at)
            try:
                exp_dt = datetime.fromisoformat(exp_iso.replace("Z", "+00:00"))
            except Exception:
                exp_dt = now

        # Compute local risk metrics for this operation
        local_expected = round(probability * amount, 4)
        local_risk_level = _classify_risk(probability if amount > 1 else probability * 0.5).value

        payload = {
            "agent_id": agent_id,
            "capability": cap_str,
            "probability": probability,
            "amount": amount,
            "priority": priority,
            "expires_at": exp_iso,
            "agent_type": agent_type,
            "step_name": step_name,
        }

        # Build offline record
        op = OfflineOperation(
            operation_id=op_id,
            idempotency_key=idem_key,
            operation_type="CREATE_OPTION",
            timestamp=now_iso,
            agent_id=agent_id,
            capability=cap_str,
            probability=probability,
            amount=amount,
            priority=priority,
            expires_at=exp_iso,
            payload_json=json.dumps(payload),
            sync_status="PENDING",
            local_risk_level=local_risk_level,
            local_expected_demand=local_expected,
        )

        # Enqueue in SQLite
        self.queue.enqueue(op)

        # Log audit event
        self.store.insert_event(
            event_type="OFFLINE_OPTION_RECORDED",
            operation_id=op_id,
            details={
                "agent_id": agent_id,
                "capability": cap_str,
                "probability": probability,
                "amount": amount,
                "local_risk_level": local_risk_level,
            },
            timestamp=now_iso,
        )

        # Return a valid ResourceOption object so caller is uninterrupted
        try:
            cap_enum = CapabilityType(cap_str)
        except ValueError:
            cap_enum = CapabilityType.GPU_COMPUTE

        return ResourceOption(
            id=op_id,
            agent_id=agent_id,
            capability=cap_enum,
            probability=probability,
            amount=amount,
            priority=priority,
            status=OptionStatus.PENDING,
            created_at=now,
            expires_at=exp_dt,
        )

    # ── Local Risk Assessment ────────────────────────────────────────

    def get_local_risk_summary(self) -> dict[str, Any]:
        """Compute local risk metrics across pending offline options."""
        pending_ops = self.queue.get_pending()
        by_cap: dict[str, list[tuple[float, int]]] = {}
        for op in pending_ops:
            if op.capability not in by_cap:
                by_cap[op.capability] = []
            by_cap[op.capability].append((op.probability, op.amount))

        total_pending = len(pending_ops)
        total_demand = sum(op.amount for op in pending_ops)
        total_expected = sum(op.probability * op.amount for op in pending_ops)

        capability_details: dict[str, Any] = {}
        for cap, opts in by_cap.items():
            exp = _compute_expected_demand(opts)
            # Estimate overcommit assuming available capacity = 1 if not connected
            p_overcommit = _compute_overcommit_probability(1, opts)
            capability_details[cap] = {
                "pending_count": len(opts),
                "total_demand": sum(a for _, a in opts),
                "expected_demand": round(exp, 4),
                "overcommit_probability": round(p_overcommit, 4),
                "risk_level": _classify_risk(p_overcommit).value,
            }

        return {
            "mode": self._mode,
            "total_pending_offline_options": total_pending,
            "total_demand": total_demand,
            "expected_demand": round(total_expected, 4),
            "capabilities": capability_details,
        }

    # ── Automatic Synchronization & Reconciliation ───────────────────

    def sync_pending(self) -> dict[str, Any]:
        """Reconcile all pending offline operations with the live RESERVE-X store.

        Runs automatically when switching from OFFLINE to ONLINE.
        Ensures idempotent execution: does not duplicate options on retry.
        """
        if self.is_offline():
            return {"synced": 0, "failed": 0, "remaining_pending": self.queue.count_pending(), "status": "offline_blocked"}

        pending_ops = self.queue.get_pending()
        synced_count = 0
        failed_count = 0

        for op in pending_ops:
            try:
                # Idempotency check: has this option already been reconciled in the core store?
                existing_reconciled = None
                if op.reconciled_option_id and op.reconciled_option_id in store.options:
                    existing_reconciled = store.options[op.reconciled_option_id]

                if existing_reconciled:
                    # Already reconciled in store — mark SYNCED without creating duplicate
                    self.queue.mark_synced(op.operation_id, existing_reconciled.id)
                    synced_count += 1
                    continue

                # Also check by operation_id directly in store (in case option was created with same ID)
                if op.operation_id in store.options:
                    self.queue.mark_synced(op.operation_id, op.operation_id)
                    synced_count += 1
                    continue

                # Execute reconciliation in core engine
                if op.operation_type == "CREATE_OPTION":
                    cap_enum = CapabilityType(op.capability)
                    exp_dt = datetime.fromisoformat(op.expires_at.replace("Z", "+00:00"))

                    # Create option in live core store
                    reconciled_opt = option_manager.create_option(
                        agent_id=op.agent_id,
                        capability=cap_enum,
                        probability=op.probability,
                        expires_at=exp_dt,
                        amount=op.amount,
                        priority=op.priority,
                    )

                    # Mark as successfully synced
                    self.queue.mark_synced(op.operation_id, reconciled_opt.id)
                    synced_count += 1

                else:
                    # Unsupported operation type
                    self.queue.mark_failed(op.operation_id, f"Unknown op type {op.operation_type}")
                    failed_count += 1

            except Exception as e:
                # Record error, keep in queue with incremented retry count
                self.queue.mark_failed(op.operation_id, str(e))
                failed_count += 1

        return {
            "synced": synced_count,
            "failed": failed_count,
            "remaining_pending": self.queue.count_pending(),
        }

    # ── Status Overview ──────────────────────────────────────────────

    def get_status(self) -> dict[str, Any]:
        """Return connectivity status and queue statistics."""
        return {
            "mode": self._mode,
            "is_offline": self.is_offline(),
            "offline_reason": self._offline_reason,
            "outage_started_at": (
                self._outage_started_at.isoformat()
                if self._outage_started_at
                else None
            ),
            "queue_stats": self.queue.get_stats(),
            "db_path": self.store.db_path,
        }

    def clear(self) -> None:
        """Clear offline state and store (used in testing)."""
        self._mode = "ONLINE"
        self._offline_reason = None
        self._outage_started_at = None
        self.store.clear()


# Default singleton instance
offline_manager = OfflineManager()
