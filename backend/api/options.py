"""Options API router — core RESERVE-X endpoints."""

from datetime import datetime

from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

from backend.models.enums import CapabilityType, OptionStatus
from backend.models.option import ResourceOption
from backend.models.allocation import Allocation
from backend.engine import option_manager
from backend.engine.option_manager import (
    OptionNotFoundError,
    InvalidOptionStateError,
    InsufficientCapacityError,
)

router = APIRouter(prefix="/options", tags=["options"])


# ── Request schemas ──────────────────────────────────────────────

class CreateOptionRequest(BaseModel):
    agent_id: str
    capability: CapabilityType
    probability: float = Field(ge=0.0, le=1.0)
    amount: int = Field(default=1, ge=1)
    priority: int = Field(default=0, ge=0)
    expires_at: datetime


class UpdateOptionRequest(BaseModel):
    probability: float | None = Field(default=None, ge=0.0, le=1.0)
    expires_at: datetime | None = None


# ── Endpoints ────────────────────────────────────────────────────

@router.post("", response_model=ResourceOption, status_code=201)
def create_option(req: CreateOptionRequest):
    """Create a new conditional resource option (PENDING)."""
    return option_manager.create_option(
        agent_id=req.agent_id,
        capability=req.capability,
        probability=req.probability,
        expires_at=req.expires_at,
        amount=req.amount,
        priority=req.priority,
    )


@router.get("", response_model=list[ResourceOption])
def list_options(
    agent_id: str | None = None,
    capability: CapabilityType | None = None,
    status: OptionStatus | None = None,
):
    """List options with optional filters."""
    return option_manager.list_options(
        agent_id=agent_id,
        capability=capability,
        status=status,
    )


@router.patch("/{option_id}", response_model=ResourceOption)
def update_option(option_id: str, req: UpdateOptionRequest):
    """Update probability and/or expiry on a PENDING option."""
    if req.probability is None and req.expires_at is None:
        raise HTTPException(400, "At least one of probability or expires_at required")
    try:
        return option_manager.update_option(
            option_id=option_id,
            probability=req.probability,
            expires_at=req.expires_at,
        )
    except OptionNotFoundError:
        raise HTTPException(404, f"Option {option_id} not found")
    except InvalidOptionStateError as e:
        raise HTTPException(409, str(e))


@router.post("/{option_id}/exercise", response_model=Allocation)
def exercise_option(option_id: str):
    """Exercise a PENDING option → resolve capability → create real allocation.

    Returns 409 if no capacity is available. The option remains PENDING.
    """
    try:
        return option_manager.exercise_option(option_id)
    except OptionNotFoundError:
        raise HTTPException(404, f"Option {option_id} not found")
    except InvalidOptionStateError as e:
        raise HTTPException(409, str(e))
    except InsufficientCapacityError as e:
        raise HTTPException(409, str(e))


@router.post("/{option_id}/cancel", response_model=ResourceOption)
def cancel_option(option_id: str):
    """Cancel a PENDING option. No resource was consumed."""
    try:
        return option_manager.cancel_option(option_id)
    except OptionNotFoundError:
        raise HTTPException(404, f"Option {option_id} not found")
    except InvalidOptionStateError as e:
        raise HTTPException(409, str(e))
