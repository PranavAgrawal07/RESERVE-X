"""System API router — risk, status, events, allocation release."""

from datetime import datetime, timezone

from pydantic import BaseModel
from fastapi import APIRouter, HTTPException

from backend.models.resource import Resource
from backend.models.option import ResourceOption
from backend.models.allocation import Allocation
from backend.models.risk import SystemRiskSummary
from backend.models.event import Event
from backend.models.enums import EventType
from backend.engine import risk_engine, resource_manager, option_manager
from backend.engine.allocation_manager import (
    release_allocation,
    AllocationNotFoundError,
    AllocationAlreadyReleasedError,
)
from backend.store import store

router = APIRouter(tags=["system"])


# ── Response schemas ─────────────────────────────────────────────

class SystemStatus(BaseModel):
    timestamp: datetime
    resources: list[Resource]
    options: list[ResourceOption]
    allocations: list[Allocation]
    risk: SystemRiskSummary


# ── Endpoints ────────────────────────────────────────────────────

@router.get("/risk", response_model=SystemRiskSummary)
def get_risk():
    """System-wide risk summary across all capabilities."""
    return risk_engine.compute_system_risk()


@router.get("/status", response_model=SystemStatus)
def get_status():
    """Full system snapshot: resources, options, allocations, risk."""
    return SystemStatus(
        timestamp=datetime.now(timezone.utc),
        resources=resource_manager.get_all_resources(),
        options=option_manager.list_options(),
        allocations=list(store.allocations.values()),
        risk=risk_engine.compute_system_risk(),
    )


@router.get("/events", response_model=list[Event])
def get_events(
    event_type: EventType | None = None,
    agent_id: str | None = None,
    limit: int = 50,
):
    """Event log for the dashboard activity feed. Most recent first."""
    events = list(reversed(store.events))
    if event_type is not None:
        events = [e for e in events if e.event_type == event_type]
    if agent_id is not None:
        events = [e for e in events if e.agent_id == agent_id]
    return events[:limit]


@router.post("/allocations/{allocation_id}/release", response_model=Allocation)
def release(allocation_id: str):
    """Release an active allocation — agent is done with the resource."""
    try:
        return release_allocation(allocation_id)
    except AllocationNotFoundError:
        raise HTTPException(404, f"Allocation {allocation_id} not found")
    except AllocationAlreadyReleasedError as e:
        raise HTTPException(409, str(e))
