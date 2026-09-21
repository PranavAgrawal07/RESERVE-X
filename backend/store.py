"""In-memory data store — single source of truth for the hackathon prototype.

Singleton instance. No locking needed (single-process uvicorn).
Replace this module if persistence is ever required.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from backend.models.enums import CapabilityType, EventType, OptionStatus
from backend.models.resource import Resource
from backend.models.option import ResourceOption
from backend.models.allocation import Allocation
from backend.models.event import Event


class Store:
    """In-memory data store for resources, options, allocations, and events."""

    def __init__(self) -> None:
        self.resources: dict[str, Resource] = {}
        self.options: dict[str, ResourceOption] = {}
        self.allocations: dict[str, Allocation] = {}
        self.events: list[Event] = []

    def reset(self) -> None:
        """Clear all data. Used by tests."""
        self.resources.clear()
        self.options.clear()
        self.allocations.clear()
        self.events.clear()

    # ── Query helpers ────────────────────────────────────────────

    def resources_by_capability(self, cap: CapabilityType) -> list[Resource]:
        """All resources providing a given capability, sorted by available capacity descending."""
        matching = [r for r in self.resources.values() if r.capability == cap]
        matching.sort(key=lambda r: r.available_capacity, reverse=True)
        return matching

    def pending_options(self) -> list[ResourceOption]:
        """All options with PENDING status."""
        return [o for o in self.options.values() if o.status == OptionStatus.PENDING]

    def pending_options_by_capability(self, cap: CapabilityType) -> list[ResourceOption]:
        """All pending options targeting a specific capability."""
        return [
            o
            for o in self.options.values()
            if o.status == OptionStatus.PENDING and o.capability == cap
        ]

    def active_allocations(self) -> list[Allocation]:
        """All allocations that have not been released."""
        return [a for a in self.allocations.values() if a.released_at is None]

    # ── Event logging ────────────────────────────────────────────

    def add_event(
        self,
        event_type: EventType,
        agent_id: str | None = None,
        option_id: str | None = None,
        resource_id: str | None = None,
        details: dict | None = None,
    ) -> Event:
        """Append an immutable event to the log."""
        event = Event(
            id=str(uuid4()),
            timestamp=datetime.now(timezone.utc),
            event_type=event_type,
            agent_id=agent_id,
            option_id=option_id,
            resource_id=resource_id,
            details=details or {},
        )
        self.events.append(event)
        return event


# Module-level singleton
store = Store()
