"""Allocation manager — release active allocations."""

from __future__ import annotations

from datetime import datetime, timezone

from backend.models.allocation import Allocation
from backend.models.enums import EventType
from backend.store import store


class AllocationError(Exception):
    """Base error for allocation operations."""


class AllocationNotFoundError(AllocationError):
    """Raised when the allocation ID does not exist."""


class AllocationAlreadyReleasedError(AllocationError):
    """Raised when trying to release an already-released allocation."""


def release_allocation(allocation_id: str) -> Allocation:
    """Release an active allocation — agent is done with the resource.

    Decrements the resource's allocated_capacity.
    """
    allocation = store.allocations.get(allocation_id)
    if allocation is None:
        raise AllocationNotFoundError(f"Allocation {allocation_id} not found")
    if allocation.released_at is not None:
        raise AllocationAlreadyReleasedError(
            f"Allocation {allocation_id} already released"
        )

    allocation.released_at = datetime.now(timezone.utc)

    # Give capacity back to the resource
    resource = store.resources.get(allocation.resource_id)
    if resource is not None:
        resource.allocated_capacity = max(
            0, resource.allocated_capacity - allocation.amount
        )

    store.add_event(
        EventType.ALLOCATION_RELEASED,
        agent_id=allocation.agent_id,
        option_id=allocation.option_id,
        resource_id=allocation.resource_id,
        details={"allocation_id": allocation.id, "amount": allocation.amount},
    )
    return allocation
