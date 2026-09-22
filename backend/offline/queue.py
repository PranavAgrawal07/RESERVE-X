"""Durable synchronization queue backed by SQLite.

Ensures at-least-once, idempotent delivery of offline operations to the core RESERVE-X engine
once network connectivity is restored.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from backend.offline.store import OfflineOperation, OfflineStore


class DurableSyncQueue:
    """Manages the lifecycle and state transitions of offline operations waiting for sync."""

    def __init__(self, store: OfflineStore):
        self.store = store

    def enqueue(self, op: OfflineOperation) -> OfflineOperation:
        """Enqueue an operation for later synchronization.
        
        If an operation with the same idempotency key already exists, returns the existing record.
        """
        existing = self.store.get_operation_by_idempotency_key(op.idempotency_key)
        if existing:
            return existing

        self.store.insert_operation(op)
        self.store.insert_event(
            event_type="OFFLINE_OPERATION_ENQUEUED",
            operation_id=op.operation_id,
            details={
                "operation_type": op.operation_type,
                "agent_id": op.agent_id,
                "capability": op.capability,
                "probability": op.probability,
                "amount": op.amount,
            },
            timestamp=op.timestamp,
        )
        return op

    def get_pending(self) -> list[OfflineOperation]:
        """Retrieve all operations ready for synchronization in FIFO order."""
        return self.store.get_pending_operations()

    def mark_synced(self, operation_id: str, reconciled_option_id: str) -> None:
        """Mark an operation as successfully synchronized and reconciled."""
        synced_at = datetime.now(timezone.utc).isoformat()
        self.store.update_operation_sync_status(
            operation_id=operation_id,
            sync_status="SYNCED",
            reconciled_option_id=reconciled_option_id,
            synced_at=synced_at,
            error_message=None,
        )
        self.store.insert_event(
            event_type="OFFLINE_OPERATION_SYNCED",
            operation_id=operation_id,
            details={
                "reconciled_option_id": reconciled_option_id,
                "synced_at": synced_at,
            },
            timestamp=synced_at,
        )

    def mark_failed(self, operation_id: str, error_message: str) -> None:
        """Record a synchronization failure and increment retry count."""
        op = self.store.get_operation(operation_id)
        current_retries = op.retry_count if op else 0
        new_retries = current_retries + 1
        now_ts = datetime.now(timezone.utc).isoformat()

        self.store.update_operation_sync_status(
            operation_id=operation_id,
            sync_status="FAILED",
            retry_count=new_retries,
            error_message=error_message,
        )
        self.store.insert_event(
            event_type="OFFLINE_OPERATION_SYNC_FAILED",
            operation_id=operation_id,
            details={
                "retry_count": new_retries,
                "error": error_message,
            },
            timestamp=now_ts,
        )

    def get_all(self, limit: int = 100) -> list[OfflineOperation]:
        """List all operations regardless of status."""
        return self.store.list_operations(limit=limit)

    def count_pending(self) -> int:
        """Count operations still pending synchronization."""
        return len(self.store.get_pending_operations())

    def count_synced(self) -> int:
        """Count successfully synced operations."""
        return len(self.store.list_operations(status="SYNCED"))

    def get_stats(self) -> dict[str, int]:
        """Return summary counts of queue statuses."""
        all_ops = self.store.list_operations(limit=1000)
        pending = sum(1 for op in all_ops if op.sync_status == "PENDING")
        failed = sum(1 for op in all_ops if op.sync_status == "FAILED")
        synced = sum(1 for op in all_ops if op.sync_status == "SYNCED")
        return {
            "total": len(all_ops),
            "pending": pending,
            "failed": failed,
            "synced": synced,
        }
