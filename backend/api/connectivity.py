"""Connectivity API router — controls and monitors offline resilience.

Provides endpoints to:
- Toggle simulated connectivity (ONLINE / OFFLINE).
- Inspect synchronization queue and offline audit events.
- Inspect local risk assessments for offline operations.
- Request offline options directly or invoke local learned predictions.
"""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field

from fastapi import APIRouter, HTTPException

from backend.models.enums import CapabilityType
from backend.models.option import ResourceOption
from backend.offline.manager import offline_manager

router = APIRouter(prefix="/connectivity", tags=["connectivity"])


# ── Schemas ──────────────────────────────────────────────────────

class SetModeRequest(BaseModel):
    mode: str = Field(..., pattern="^(ONLINE|OFFLINE)$")
    reason: str | None = "MANUAL"


class LocalPredictRequest(BaseModel):
    agent_type: str
    step_name: str
    current_capability: str


# ── Endpoints ────────────────────────────────────────────────────

@router.get("/status")
def get_connectivity_status():
    """Retrieve current connectivity state and sync queue statistics."""
    return offline_manager.get_status()


@router.post("/mode")
def set_connectivity_mode(req: SetModeRequest):
    """Set connectivity mode to ONLINE or OFFLINE."""
    if req.mode == "OFFLINE":
        offline_manager.set_offline(reason=req.reason or "MANUAL")
        return offline_manager.get_status()
    else:
        return offline_manager.set_online()


@router.post("/offline")
def switch_offline(reason: str | None = None):
    """Switch system to simulated or real OFFLINE mode."""
    offline_manager.set_offline(reason=reason or "MANUAL")
    return offline_manager.get_status()


@router.post("/online")
def switch_online():
    """Switch system to ONLINE mode and trigger automatic synchronization."""
    return offline_manager.set_online()


@router.get("/queue")
def list_queue(status: str | None = None, limit: int = 100):
    """List offline operations in the durable SQLite synchronization queue."""
    ops = offline_manager.store.list_operations(status=status, limit=limit)
    return [op.to_dict() for op in ops]


@router.get("/events")
def list_offline_events(limit: int = 100):
    """List offline audit events from SQLite."""
    events = offline_manager.store.list_events(limit=limit)
    return [e.to_dict() for e in events]


@router.get("/risk")
def get_local_risk():
    """Get local risk assessment across all pending offline operations."""
    return offline_manager.get_local_risk_summary()


@router.post("/predict")
def local_predict(req: LocalPredictRequest):
    """Use local LearnedPredictor to predict capability and confidence."""
    return offline_manager.predict_capability(
        agent_type=req.agent_type,
        step_name=req.step_name,
        current_capability=req.current_capability,
    )


@router.post("/sync")
def trigger_sync():
    """Explicitly trigger synchronization of pending operations."""
    if offline_manager.is_offline():
        raise HTTPException(
            status_code=400,
            detail="Cannot synchronize while system is in OFFLINE mode.",
        )
    return offline_manager.sync_pending()
