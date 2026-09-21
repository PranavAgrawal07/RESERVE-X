"""Resource manager — register and query scarce resources."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from backend.models.enums import CapabilityType, EventType
from backend.models.resource import Resource
from backend.store import store


def register_resource(
    name: str,
    capability: CapabilityType,
    total_capacity: int,
) -> Resource:
    """Register a new resource with the system."""
    resource = Resource(
        id=str(uuid4()),
        name=name,
        capability=capability,
        total_capacity=total_capacity,
        allocated_capacity=0,
        created_at=datetime.now(timezone.utc),
    )
    store.resources[resource.id] = resource
    store.add_event(
        EventType.RESOURCE_REGISTERED,
        resource_id=resource.id,
        details={"name": name, "capability": capability.value, "capacity": total_capacity},
    )
    return resource


def get_all_resources() -> list[Resource]:
    """Return all registered resources."""
    return list(store.resources.values())


def get_resource(resource_id: str) -> Resource | None:
    """Return a single resource by ID, or None."""
    return store.resources.get(resource_id)
