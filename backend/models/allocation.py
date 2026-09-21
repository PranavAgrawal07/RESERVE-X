"""Allocation model — real resource consumption.

Created only when a ResourceOption is exercised.
"""

from datetime import datetime

from pydantic import BaseModel

from backend.models.enums import CapabilityType


class Allocation(BaseModel):
    """An active resource allocation (exercised option → real consumption)."""

    id: str
    option_id: str
    resource_id: str
    agent_id: str
    capability: CapabilityType
    amount: int
    allocated_at: datetime
    released_at: datetime | None = None
