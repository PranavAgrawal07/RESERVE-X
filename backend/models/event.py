"""Event model — immutable audit log entry."""

from datetime import datetime

from pydantic import BaseModel

from backend.models.enums import EventType


class Event(BaseModel):
    """A recorded system event (option created, exercised, expired, etc.)."""

    id: str
    timestamp: datetime
    event_type: EventType
    agent_id: str | None = None
    option_id: str | None = None
    resource_id: str | None = None
    details: dict = {}
