"""Resource model — a scarce resource with finite capacity."""

from datetime import datetime

from pydantic import BaseModel, computed_field

from backend.models.enums import CapabilityType


class Resource(BaseModel):
    """A concrete resource (e.g. a GPU pool) providing a capability."""

    id: str
    name: str
    capability: CapabilityType
    total_capacity: int
    allocated_capacity: int = 0
    created_at: datetime

    @computed_field
    @property
    def available_capacity(self) -> int:
        return self.total_capacity - self.allocated_capacity
