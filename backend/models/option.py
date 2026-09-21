"""ResourceOption model — the core RESERVE-X primitive.

A conditional right to obtain a capability later.  NOT an actual reservation.
"""

from datetime import datetime

from pydantic import BaseModel, Field

from backend.models.enums import CapabilityType, OptionStatus


class ResourceOption(BaseModel):
    """Conditional resource option held by an agent."""

    id: str
    agent_id: str
    capability: CapabilityType
    probability: float = Field(ge=0.0, le=1.0)
    amount: int = Field(default=1, ge=1)
    priority: int = Field(default=0, ge=0)
    status: OptionStatus = OptionStatus.PENDING
    created_at: datetime
    expires_at: datetime
    exercised_at: datetime | None = None
    cancelled_at: datetime | None = None
