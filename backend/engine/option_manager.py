"""Option manager — the heart of RESERVE-X.

Handles the full conditional-option lifecycle:
  create → update → exercise / cancel / expire
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from backend.models.enums import CapabilityType, EventType, OptionStatus
from backend.models.option import ResourceOption
from backend.models.allocation import Allocation
from backend.store import store


class OptionError(Exception):
    """Base error for option operations."""


class OptionNotFoundError(OptionError):
    """Raised when the option ID does not exist."""


class InvalidOptionStateError(OptionError):
    """Raised when a transition is invalid for the current status."""


class InsufficientCapacityError(OptionError):
    """Raised when exercise fails due to no available capacity."""


# ── Create ───────────────────────────────────────────────────────

def create_option(
    agent_id: str,
    capability: CapabilityType,
    probability: float,
    expires_at: datetime,
    amount: int = 1,
    priority: int = 0,
) -> ResourceOption:
    """Create a new conditional resource option (PENDING)."""
    option = ResourceOption(
        id=str(uuid4()),
        agent_id=agent_id,
        capability=capability,
        probability=probability,
        amount=amount,
        priority=priority,
        status=OptionStatus.PENDING,
        created_at=datetime.now(timezone.utc),
        expires_at=expires_at,
    )
    store.options[option.id] = option
    store.add_event(
        EventType.OPTION_CREATED,
        agent_id=agent_id,
        option_id=option.id,
        details={
            "capability": capability.value,
            "probability": probability,
            "amount": amount,
        },
    )
    return option


# ── Update ───────────────────────────────────────────────────────

def update_option(
    option_id: str,
    probability: float | None = None,
    expires_at: datetime | None = None,
) -> ResourceOption:
    """Update probability and/or expiry on a PENDING option."""
    option = _get_option(option_id)
    if option.status != OptionStatus.PENDING:
        raise InvalidOptionStateError(
            f"Cannot update option in {option.status.value} state"
        )

    old_probability = option.probability
    if probability is not None:
        option.probability = probability
    if expires_at is not None:
        option.expires_at = expires_at

    store.add_event(
        EventType.OPTION_UPDATED,
        agent_id=option.agent_id,
        option_id=option.id,
        details={
            "old_probability": old_probability,
            "new_probability": option.probability,
        },
    )
    return option


# ── Exercise (critical path) ────────────────────────────────────

def exercise_option(option_id: str) -> Allocation:
    """Exercise a PENDING option → resolve capability → allocate real resource.

    Returns the created Allocation on success.
    Raises InsufficientCapacityError if no resource can satisfy the request.
    The option remains PENDING on failure (agent can retry or cancel).
    """
    option = _get_option(option_id)
    if option.status != OptionStatus.PENDING:
        raise InvalidOptionStateError(
            f"Cannot exercise option in {option.status.value} state"
        )

    # Find best resource: most available capacity first
    candidates = store.resources_by_capability(option.capability)

    for resource in candidates:
        if resource.available_capacity >= option.amount:
            # ── Success: convert option → allocation ──
            option.status = OptionStatus.EXERCISED
            option.exercised_at = datetime.now(timezone.utc)

            allocation = Allocation(
                id=str(uuid4()),
                option_id=option.id,
                resource_id=resource.id,
                agent_id=option.agent_id,
                capability=option.capability,
                amount=option.amount,
                allocated_at=datetime.now(timezone.utc),
            )
            resource.allocated_capacity += option.amount
            store.allocations[allocation.id] = allocation

            store.add_event(
                EventType.OPTION_EXERCISED,
                agent_id=option.agent_id,
                option_id=option.id,
                resource_id=resource.id,
            )
            store.add_event(
                EventType.ALLOCATION_CREATED,
                agent_id=option.agent_id,
                option_id=option.id,
                resource_id=resource.id,
                details={"allocation_id": allocation.id, "amount": option.amount},
            )
            return allocation

    # ── Failure: no capacity ──
    store.add_event(
        EventType.EXERCISE_FAILED,
        agent_id=option.agent_id,
        option_id=option.id,
        details={
            "reason": "insufficient_capacity",
            "capability": option.capability.value,
            "amount_requested": option.amount,
        },
    )
    raise InsufficientCapacityError(
        f"No available capacity for {option.capability.value} "
        f"(requested {option.amount} unit(s))"
    )


# ── Cancel ───────────────────────────────────────────────────────

def cancel_option(option_id: str) -> ResourceOption:
    """Cancel a PENDING option. No resource was consumed."""
    option = _get_option(option_id)
    if option.status != OptionStatus.PENDING:
        raise InvalidOptionStateError(
            f"Cannot cancel option in {option.status.value} state"
        )
    option.status = OptionStatus.CANCELLED
    option.cancelled_at = datetime.now(timezone.utc)
    store.add_event(
        EventType.OPTION_CANCELLED,
        agent_id=option.agent_id,
        option_id=option.id,
    )
    return option


# ── Expire ───────────────────────────────────────────────────────

def expire_stale_options() -> list[ResourceOption]:
    """Expire all PENDING options whose expires_at is in the past.

    Called by the background sweep and/or explicitly by the simulation.
    Returns the list of options that were expired.
    """
    now = datetime.now(timezone.utc)
    expired: list[ResourceOption] = []
    for option in store.pending_options():
        if option.expires_at <= now:
            option.status = OptionStatus.EXPIRED
            store.add_event(
                EventType.OPTION_EXPIRED,
                agent_id=option.agent_id,
                option_id=option.id,
                details={"expired_at": now.isoformat()},
            )
            expired.append(option)
    return expired


# ── Query helpers ────────────────────────────────────────────────

def get_option(option_id: str) -> ResourceOption | None:
    """Public: get option by ID or None."""
    return store.options.get(option_id)


def list_options(
    agent_id: str | None = None,
    capability: CapabilityType | None = None,
    status: OptionStatus | None = None,
) -> list[ResourceOption]:
    """List options with optional filters."""
    result = list(store.options.values())
    if agent_id is not None:
        result = [o for o in result if o.agent_id == agent_id]
    if capability is not None:
        result = [o for o in result if o.capability == capability]
    if status is not None:
        result = [o for o in result if o.status == status]
    return result


# ── Internal ─────────────────────────────────────────────────────

def _get_option(option_id: str) -> ResourceOption:
    """Internal: get option or raise."""
    option = store.options.get(option_id)
    if option is None:
        raise OptionNotFoundError(f"Option {option_id} not found")
    return option
