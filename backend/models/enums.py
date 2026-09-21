"""RESERVE-X enumerations."""

from enum import Enum


class CapabilityType(str, Enum):
    """Abstract capability an agent might need."""

    GPU_COMPUTE = "GPU_COMPUTE"
    CODE_EXECUTION = "CODE_EXECUTION"
    WEB_SEARCH = "WEB_SEARCH"
    LLM_INFERENCE = "LLM_INFERENCE"


class OptionStatus(str, Enum):
    """Lifecycle status of a ResourceOption."""

    PENDING = "PENDING"
    EXERCISED = "EXERCISED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class RiskLevel(str, Enum):
    """Qualitative risk classification."""

    LOW = "LOW"          # P(overcommit) < 0.10
    MEDIUM = "MEDIUM"    # 0.10 <= P < 0.30
    HIGH = "HIGH"        # 0.30 <= P < 0.60
    CRITICAL = "CRITICAL"  # P >= 0.60


class EventType(str, Enum):
    """Types of system events logged for the activity feed."""

    OPTION_CREATED = "OPTION_CREATED"
    OPTION_EXERCISED = "OPTION_EXERCISED"
    OPTION_EXPIRED = "OPTION_EXPIRED"
    OPTION_CANCELLED = "OPTION_CANCELLED"
    OPTION_UPDATED = "OPTION_UPDATED"
    EXERCISE_FAILED = "EXERCISE_FAILED"
    ALLOCATION_CREATED = "ALLOCATION_CREATED"
    ALLOCATION_RELEASED = "ALLOCATION_RELEASED"
    RESOURCE_REGISTERED = "RESOURCE_REGISTERED"
