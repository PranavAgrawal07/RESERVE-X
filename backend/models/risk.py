"""Risk report models."""

from datetime import datetime

from pydantic import BaseModel

from backend.models.enums import CapabilityType, RiskLevel


class RiskReport(BaseModel):
    """Risk analysis for a single capability across all resources providing it."""

    capability: CapabilityType
    resource_ids: list[str]
    total_capacity: int
    allocated_capacity: int
    available_capacity: int
    pending_options_count: int
    total_pending_demand: int
    expected_demand: float
    overcommit_probability: float
    risk_level: RiskLevel


class SystemRiskSummary(BaseModel):
    """Aggregate risk view across all capabilities."""

    timestamp: datetime
    capability_risks: list[RiskReport]
    highest_risk_level: RiskLevel
    total_pending_options: int
    total_active_allocations: int
