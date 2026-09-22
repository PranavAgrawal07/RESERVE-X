"""SQLite-based durable local store for offline operations and events.

Provides ACID persistence for offline requests, durable synchronization queue entries,
and audit logs during connectivity outages.
"""

from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass
class OfflineOperation:
    """Represents a critical agent operation captured while offline."""

    operation_id: str
    idempotency_key: str
    operation_type: str
    timestamp: str
    agent_id: str
    capability: str
    probability: float
    amount: int
    priority: int
    expires_at: str
    payload_json: str
    sync_status: str  # "PENDING", "SYNCED", "FAILED"
    retry_count: int = 0
    error_message: str | None = None
    synced_at: str | None = None
    reconciled_option_id: str | None = None
    local_risk_level: str | None = None
    local_expected_demand: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class OfflineEvent:
    """Represents an audit event logged during offline operation or sync."""

    event_id: str
    operation_id: str | None
    event_type: str
    timestamp: str
    details_json: str

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        try:
            d["details"] = json.loads(self.details_json)
        except Exception:
            d["details"] = {}
        return d


class OfflineStore:
    """Durable SQLite storage engine for offline operations and sync logs."""

    def __init__(self, db_path: str = "data/offline_resilience.db"):
        self.db_path = db_path
        if db_path != ":memory:":
            os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self) -> None:
        """Create tables and indexes if they do not exist."""
        with self._conn:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS offline_operations (
                    operation_id TEXT PRIMARY KEY,
                    idempotency_key TEXT UNIQUE,
                    operation_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    capability TEXT NOT NULL,
                    probability REAL NOT NULL,
                    amount INTEGER NOT NULL DEFAULT 1,
                    priority INTEGER NOT NULL DEFAULT 0,
                    expires_at TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    sync_status TEXT NOT NULL DEFAULT 'PENDING',
                    retry_count INTEGER NOT NULL DEFAULT 0,
                    error_message TEXT,
                    synced_at TEXT,
                    reconciled_option_id TEXT,
                    local_risk_level TEXT,
                    local_expected_demand REAL
                )
                """
            )
            self._conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_offline_ops_status
                ON offline_operations(sync_status, timestamp)
                """
            )
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS offline_events (
                    event_id TEXT PRIMARY KEY,
                    operation_id TEXT,
                    event_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    details_json TEXT NOT NULL
                )
                """
            )
            self._conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_offline_events_ts
                ON offline_events(timestamp)
                """
            )

    def insert_operation(self, op: OfflineOperation) -> OfflineOperation:
        """Insert a new offline operation into SQLite."""
        with self._conn:
            self._conn.execute(
                """
                INSERT INTO offline_operations (
                    operation_id, idempotency_key, operation_type, timestamp,
                    agent_id, capability, probability, amount, priority,
                    expires_at, payload_json, sync_status, retry_count,
                    error_message, synced_at, reconciled_option_id,
                    local_risk_level, local_expected_demand
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
                """,
                (
                    op.operation_id,
                    op.idempotency_key,
                    op.operation_type,
                    op.timestamp,
                    op.agent_id,
                    op.capability,
                    op.probability,
                    op.amount,
                    op.priority,
                    op.expires_at,
                    op.payload_json,
                    op.sync_status,
                    op.retry_count,
                    op.error_message,
                    op.synced_at,
                    op.reconciled_option_id,
                    op.local_risk_level,
                    op.local_expected_demand,
                ),
            )
        return op

    def get_operation(self, operation_id: str) -> OfflineOperation | None:
        """Fetch operation by primary key."""
        cursor = self._conn.execute(
            "SELECT * FROM offline_operations WHERE operation_id = ?",
            (operation_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return self._row_to_operation(row)

    def get_operation_by_idempotency_key(self, key: str) -> OfflineOperation | None:
        """Fetch operation by idempotency key."""
        cursor = self._conn.execute(
            "SELECT * FROM offline_operations WHERE idempotency_key = ?",
            (key,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return self._row_to_operation(row)

    def list_operations(
        self, status: str | None = None, limit: int = 100
    ) -> list[OfflineOperation]:
        """List operations ordered by timestamp ascending."""
        if status:
            cursor = self._conn.execute(
                """
                SELECT * FROM offline_operations
                WHERE sync_status = ?
                ORDER BY timestamp ASC
                LIMIT ?
                """,
                (status, limit),
            )
        else:
            cursor = self._conn.execute(
                """
                SELECT * FROM offline_operations
                ORDER BY timestamp ASC
                LIMIT ?
                """,
                (limit,),
            )
        return [self._row_to_operation(row) for row in cursor.fetchall()]

    def get_pending_operations(self) -> list[OfflineOperation]:
        """Fetch all PENDING operations waiting for synchronization."""
        cursor = self._conn.execute(
            """
            SELECT * FROM offline_operations
            WHERE sync_status IN ('PENDING', 'FAILED')
            ORDER BY timestamp ASC
            """
        )
        return [self._row_to_operation(row) for row in cursor.fetchall()]

    def update_operation_sync_status(
        self,
        operation_id: str,
        sync_status: str,
        retry_count: int | None = None,
        error_message: str | None = None,
        reconciled_option_id: str | None = None,
        synced_at: str | None = None,
    ) -> None:
        """Update synchronization status and reconciliation details."""
        updates: list[str] = ["sync_status = ?"]
        params: list[Any] = [sync_status]

        if retry_count is not None:
            updates.append("retry_count = ?")
            params.append(retry_count)

        if error_message is not None:
            updates.append("error_message = ?")
            params.append(error_message)

        if reconciled_option_id is not None:
            updates.append("reconciled_option_id = ?")
            params.append(reconciled_option_id)

        if synced_at is not None:
            updates.append("synced_at = ?")
            params.append(synced_at)

        params.append(operation_id)
        query = f"UPDATE offline_operations SET {', '.join(updates)} WHERE operation_id = ?"

        with self._conn:
            self._conn.execute(query, params)

    def insert_event(
        self,
        event_type: str,
        operation_id: str | None = None,
        details: dict[str, Any] | None = None,
        timestamp: str | None = None,
    ) -> OfflineEvent:
        """Insert an audit event into SQLite."""
        event_id = str(uuid4())
        ts = timestamp or datetime.now(timezone.utc).isoformat()
        details_json = json.dumps(details or {})

        with self._conn:
            self._conn.execute(
                """
                INSERT INTO offline_events (
                    event_id, operation_id, event_type, timestamp, details_json
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (event_id, operation_id, event_type, ts, details_json),
            )
        return OfflineEvent(
            event_id=event_id,
            operation_id=operation_id,
            event_type=event_type,
            timestamp=ts,
            details_json=details_json,
        )

    def list_events(self, limit: int = 100) -> list[OfflineEvent]:
        """List offline events, most recent first."""
        cursor = self._conn.execute(
            """
            SELECT * FROM offline_events
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (limit,),
        )
        return [
            OfflineEvent(
                event_id=row["event_id"],
                operation_id=row["operation_id"],
                event_type=row["event_type"],
                timestamp=row["timestamp"],
                details_json=row["details_json"],
            )
            for row in cursor.fetchall()
        ]

    def clear(self) -> None:
        """Clear all stored offline data (used in tests)."""
        with self._conn:
            self._conn.execute("DELETE FROM offline_operations")
            self._conn.execute("DELETE FROM offline_events")

    def close(self) -> None:
        """Close SQLite database connection."""
        self._conn.close()

    @staticmethod
    def _row_to_operation(row: sqlite3.Row) -> OfflineOperation:
        return OfflineOperation(
            operation_id=row["operation_id"],
            idempotency_key=row["idempotency_key"],
            operation_type=row["operation_type"],
            timestamp=row["timestamp"],
            agent_id=row["agent_id"],
            capability=row["capability"],
            probability=float(row["probability"]),
            amount=int(row["amount"]),
            priority=int(row["priority"]),
            expires_at=row["expires_at"],
            payload_json=row["payload_json"],
            sync_status=row["sync_status"],
            retry_count=int(row["retry_count"]),
            error_message=row["error_message"],
            synced_at=row["synced_at"],
            reconciled_option_id=row["reconciled_option_id"],
            local_risk_level=row["local_risk_level"],
            local_expected_demand=(
                float(row["local_expected_demand"])
                if row["local_expected_demand"] is not None
                else None
            ),
        )
