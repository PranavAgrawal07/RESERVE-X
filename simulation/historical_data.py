"""
Synthetic historical workflow dataset for the RESERVE-X Learned Predictor.

Each record represents a completed workflow execution step with context about
the agent type, current step, capability used, and the NEXT capability that
was required. This is the prediction target: given the current context, what
capability will the agent need next?

All capability values use the backend CapabilityType enum strings:
    GPU_COMPUTE, CODE_EXECUTION, WEB_SEARCH, LLM_INFERENCE,
    TESTING, TERMINAL, DATABASE, SECURITY_SCAN, DEPLOYMENT
"""

from __future__ import annotations


# Each record: (agent_type, step_name, current_capability, next_capability)
# next_capability is what the agent needed AFTER the current step — the label.
HISTORICAL_WORKFLOW_RECORDS: list[dict[str, str]] = [
    # ── Coding agent workflows ──────────────────────────────────────────
    # Pattern: TERMINAL → TESTING → LLM_INFERENCE → TESTING → DEPLOYMENT
    {"agent_type": "Coding", "step_name": "write_code",   "current_capability": "TERMINAL",       "next_capability": "TESTING"},
    {"agent_type": "Coding", "step_name": "run_tests",    "current_capability": "TESTING",         "next_capability": "LLM_INFERENCE"},
    {"agent_type": "Coding", "step_name": "debug",        "current_capability": "LLM_INFERENCE",   "next_capability": "TESTING"},
    {"agent_type": "Coding", "step_name": "run_tests",    "current_capability": "TESTING",         "next_capability": "DEPLOYMENT"},

    # Variant: skip second test round
    {"agent_type": "Coding", "step_name": "write_code",   "current_capability": "TERMINAL",       "next_capability": "TESTING"},
    {"agent_type": "Coding", "step_name": "run_tests",    "current_capability": "TESTING",         "next_capability": "LLM_INFERENCE"},
    {"agent_type": "Coding", "step_name": "debug",        "current_capability": "LLM_INFERENCE",   "next_capability": "DEPLOYMENT"},

    # Variant: extra debug cycle
    {"agent_type": "Coding", "step_name": "write_code",   "current_capability": "TERMINAL",       "next_capability": "LLM_INFERENCE"},
    {"agent_type": "Coding", "step_name": "debug",        "current_capability": "LLM_INFERENCE",   "next_capability": "TESTING"},
    {"agent_type": "Coding", "step_name": "run_tests",    "current_capability": "TESTING",         "next_capability": "DEPLOYMENT"},

    # ── Research agent workflows ────────────────────────────────────────
    # Pattern: WEB_SEARCH → LLM_INFERENCE → LLM_INFERENCE → LLM_INFERENCE
    {"agent_type": "Research", "step_name": "search_web",       "current_capability": "WEB_SEARCH",     "next_capability": "LLM_INFERENCE"},
    {"agent_type": "Research", "step_name": "analyze_sources",  "current_capability": "LLM_INFERENCE",  "next_capability": "LLM_INFERENCE"},
    {"agent_type": "Research", "step_name": "summarize",        "current_capability": "LLM_INFERENCE",  "next_capability": "LLM_INFERENCE"},

    # Variant: search → database → LLM
    {"agent_type": "Research", "step_name": "search_web",       "current_capability": "WEB_SEARCH",     "next_capability": "DATABASE"},
    {"agent_type": "Research", "step_name": "query_database",   "current_capability": "DATABASE",       "next_capability": "LLM_INFERENCE"},
    {"agent_type": "Research", "step_name": "analyze_sources",  "current_capability": "LLM_INFERENCE",  "next_capability": "LLM_INFERENCE"},

    # Variant: web → LLM → web → LLM
    {"agent_type": "Research", "step_name": "search_web",       "current_capability": "WEB_SEARCH",     "next_capability": "LLM_INFERENCE"},
    {"agent_type": "Research", "step_name": "analyze_sources",  "current_capability": "LLM_INFERENCE",  "next_capability": "WEB_SEARCH"},
    {"agent_type": "Research", "step_name": "search_web",       "current_capability": "WEB_SEARCH",     "next_capability": "LLM_INFERENCE"},

    # ── Testing agent workflows ─────────────────────────────────────────
    # Pattern: TESTING → TESTING → TERMINAL → LLM_INFERENCE
    {"agent_type": "Testing", "step_name": "prepare_tests",    "current_capability": "TESTING",        "next_capability": "TESTING"},
    {"agent_type": "Testing", "step_name": "run_tests",        "current_capability": "TESTING",        "next_capability": "TERMINAL"},
    {"agent_type": "Testing", "step_name": "inspect_failures", "current_capability": "TERMINAL",       "next_capability": "LLM_INFERENCE"},

    # Variant: immediate LLM after test
    {"agent_type": "Testing", "step_name": "prepare_tests",    "current_capability": "TESTING",        "next_capability": "TESTING"},
    {"agent_type": "Testing", "step_name": "run_tests",        "current_capability": "TESTING",        "next_capability": "LLM_INFERENCE"},

    # Variant: long test cycle
    {"agent_type": "Testing", "step_name": "prepare_tests",    "current_capability": "TESTING",        "next_capability": "TESTING"},
    {"agent_type": "Testing", "step_name": "run_tests",        "current_capability": "TESTING",        "next_capability": "TESTING"},
    {"agent_type": "Testing", "step_name": "run_tests",        "current_capability": "TESTING",        "next_capability": "TERMINAL"},

    # ── Security agent workflows ────────────────────────────────────────
    # Pattern: SECURITY_SCAN → LLM_INFERENCE → TESTING → LLM_INFERENCE
    {"agent_type": "Security", "step_name": "scan_code",              "current_capability": "SECURITY_SCAN",  "next_capability": "LLM_INFERENCE"},
    {"agent_type": "Security", "step_name": "analyze_vulnerability",  "current_capability": "LLM_INFERENCE",  "next_capability": "TESTING"},
    {"agent_type": "Security", "step_name": "run_security_tests",     "current_capability": "TESTING",        "next_capability": "LLM_INFERENCE"},

    # Variant: scan → scan → LLM
    {"agent_type": "Security", "step_name": "scan_code",              "current_capability": "SECURITY_SCAN",  "next_capability": "SECURITY_SCAN"},
    {"agent_type": "Security", "step_name": "scan_code",              "current_capability": "SECURITY_SCAN",  "next_capability": "LLM_INFERENCE"},

    # Variant: scan → LLM → LLM
    {"agent_type": "Security", "step_name": "scan_code",              "current_capability": "SECURITY_SCAN",  "next_capability": "LLM_INFERENCE"},
    {"agent_type": "Security", "step_name": "analyze_vulnerability",  "current_capability": "LLM_INFERENCE",  "next_capability": "LLM_INFERENCE"},

    # ── Data Analysis agent workflows ───────────────────────────────────
    # Pattern: DATABASE → DATABASE → GPU_COMPUTE → LLM_INFERENCE
    {"agent_type": "Data Analysis", "step_name": "load_data",        "current_capability": "DATABASE",       "next_capability": "DATABASE"},
    {"agent_type": "Data Analysis", "step_name": "query_database",   "current_capability": "DATABASE",       "next_capability": "GPU_COMPUTE"},
    {"agent_type": "Data Analysis", "step_name": "analyze_data",     "current_capability": "GPU_COMPUTE",    "next_capability": "LLM_INFERENCE"},

    # Variant: database → GPU → GPU → LLM
    {"agent_type": "Data Analysis", "step_name": "load_data",        "current_capability": "DATABASE",       "next_capability": "GPU_COMPUTE"},
    {"agent_type": "Data Analysis", "step_name": "analyze_data",     "current_capability": "GPU_COMPUTE",    "next_capability": "GPU_COMPUTE"},
    {"agent_type": "Data Analysis", "step_name": "analyze_data",     "current_capability": "GPU_COMPUTE",    "next_capability": "LLM_INFERENCE"},

    # Variant: database → LLM → database → GPU
    {"agent_type": "Data Analysis", "step_name": "load_data",        "current_capability": "DATABASE",       "next_capability": "LLM_INFERENCE"},
    {"agent_type": "Data Analysis", "step_name": "summarize",        "current_capability": "LLM_INFERENCE",  "next_capability": "DATABASE"},
    {"agent_type": "Data Analysis", "step_name": "query_database",   "current_capability": "DATABASE",       "next_capability": "GPU_COMPUTE"},
]


def get_training_data() -> list[dict[str, str]]:
    """
    Return the full historical workflow dataset.

    Each record is a dict with keys:
        - agent_type: Type of agent (e.g. 'Coding', 'Research')
        - step_name: Name of the workflow step (e.g. 'write_code', 'run_tests')
        - current_capability: The backend capability used at this step
        - next_capability: The backend capability needed next (prediction target)

    Returns:
        list[dict[str, str]]: The complete training dataset.
    """
    return HISTORICAL_WORKFLOW_RECORDS.copy()


# Valid backend capability types for validation
VALID_CAPABILITIES: list[str] = [
    "GPU_COMPUTE",
    "CODE_EXECUTION",
    "WEB_SEARCH",
    "LLM_INFERENCE",
    "TESTING",
    "TERMINAL",
    "DATABASE",
    "SECURITY_SCAN",
    "DEPLOYMENT",
]
