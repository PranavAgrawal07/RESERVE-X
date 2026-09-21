"""
Resource to RESERVE-X capability definitions and mapping utilities.
"""
from __future__ import annotations

# Canonical mapping from simulation resource names to RESERVE-X capability names
RESOURCE_TO_CAPABILITY_MAP: dict[str, str] = {
    "LLM": "LLM_INFERENCE",
    "GPU": "GPU_COMPUTE",
    "testing_environment": "TESTING",
    "terminal": "TERMINAL",
    "database": "DATABASE",
    "security_scanner": "SECURITY_SCAN",
    "search_tool": "WEB_SEARCH",
    "deployment_environment": "DEPLOYMENT",
}


def map_resource_to_capability(resource: str) -> str:
    """
    Map a simulator resource name to its corresponding RESERVE-X capability.

    Args:
        resource: The simulator resource name (e.g. 'LLM', 'GPU').

    Returns:
        str: The RESERVE-X capability string (e.g. 'LLM_INFERENCE', 'GPU_COMPUTE').

    Raises:
        ValueError: If the resource name is unknown or unsupported.
    """
    if resource in RESOURCE_TO_CAPABILITY_MAP:
        return RESOURCE_TO_CAPABILITY_MAP[resource]
    raise ValueError(
        f"Unknown or unsupported resource '{resource}'. "
        f"Valid resources are: {list(RESOURCE_TO_CAPABILITY_MAP.keys())}"
    )


def is_supported_resource(resource: str) -> bool:
    """
    Check whether a given resource name has a valid RESERVE-X capability mapping.
    """
    return resource in RESOURCE_TO_CAPABILITY_MAP
