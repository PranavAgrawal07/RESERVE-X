"""What-If Simulation API router — hypothetical risk analysis.

Provides a read-only endpoint that computes hypothetical overcommit risk
for user-specified scenarios WITHOUT mutating any backend state (no options
created, no allocations made, no resources modified).

Uses the same mathematical primitives as the real risk engine:
    - _compute_overcommit_probability (exact 2^n subset enumeration)
    - _compute_expected_demand (E[demand] = sum(p_i * a_i))
    - _classify_risk (probability → RiskLevel mapping)
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from fastapi import APIRouter

from backend.models.enums import RiskLevel
from backend.engine.risk_engine import (
    _classify_risk,
    _compute_expected_demand,
    _compute_overcommit_probability,
    compute_system_risk,
)
from backend.store import store

router = APIRouter(tags=["simulation"])


# ── Request / Response schemas ───────────────────────────────────

class WhatIfRequest(BaseModel):
    """Parameters for a hypothetical what-if scenario."""

    agent_count: int = Field(
        ..., ge=0, le=50,
        description="Number of hypothetical agents, each creating one option.",
    )
    resource_capacity: int = Field(
        ..., ge=0,
        description="Hypothetical total available resource capacity.",
    )
    average_probability: float = Field(
        ..., ge=0.0, le=1.0,
        description="Average exercise probability for each hypothetical option.",
    )


class WhatIfMetrics(BaseModel):
    """Risk metrics for one side of the comparison."""

    capacity: int
    pending_options: int | None = None
    agent_count: int | None = None
    expected_demand: float
    overcommit_probability: float
    risk_level: RiskLevel


class WhatIfResponse(BaseModel):
    """Side-by-side comparison of current state and hypothetical scenario."""

    current: WhatIfMetrics
    scenario: WhatIfMetrics


def _safe_compute_overcommit_probability(
    available_capacity: int,
    options: list[tuple[float, int]],
) -> float:
    """Compute overcommit probability.
    
    Uses exact 2^n enumeration (_compute_overcommit_probability) for n <= 15.
    For n > 15, uses exact convolution DP which computes the identical mathematical
    distribution in O(n * demand) instead of 2^n iterations.
    """
    n = len(options)
    if n == 0 or available_capacity < 0:
        return 0.0
    if n <= 15:
        return _compute_overcommit_probability(available_capacity, options)
    dp = {0: 1.0}
    for p, a in options:
        next_dp: dict[int, float] = {}
        for d, prob in dp.items():
            next_dp[d] = next_dp.get(d, 0.0) + prob * (1.0 - p)
            next_dp[d + a] = next_dp.get(d + a, 0.0) + prob * p
        dp = next_dp
    return sum(prob for d, prob in dp.items() if d > available_capacity)


# ── Endpoint ─────────────────────────────────────────────────────

@router.post("/simulation/what-if", response_model=WhatIfResponse)
def run_what_if(req: WhatIfRequest):
    """Compute hypothetical risk WITHOUT mutating any backend state.

    - ``current`` reflects real system state (live resources, pending options).
    - ``scenario`` reflects the hypothetical parameters the user supplied.
    """

    # ── Current state (read-only snapshot) ────────────────────────
    system_risk = compute_system_risk()

    # Aggregate across all capabilities
    current_capacity = sum(
        r.available_capacity
        for r in store.resources.values()
    )
    pending = store.pending_options()
    current_options_data = [(o.probability, o.amount) for o in pending]
    current_expected = _compute_expected_demand(current_options_data)
    current_overcommit = _safe_compute_overcommit_probability(
        current_capacity, current_options_data
    )

    current_metrics = WhatIfMetrics(
        capacity=current_capacity,
        pending_options=len(pending),
        expected_demand=round(current_expected, 4),
        overcommit_probability=round(current_overcommit, 6),
        risk_level=_classify_risk(current_overcommit),
    )

    # ── Scenario (purely hypothetical — no state mutation) ────────
    # Each hypothetical agent creates one option with amount=1
    scenario_options = [
        (req.average_probability, 1) for _ in range(req.agent_count)
    ]
    scenario_expected = _compute_expected_demand(scenario_options)
    scenario_overcommit = _safe_compute_overcommit_probability(
        req.resource_capacity, scenario_options
    )

    scenario_metrics = WhatIfMetrics(
        capacity=req.resource_capacity,
        agent_count=req.agent_count,
        expected_demand=round(scenario_expected, 4),
        overcommit_probability=round(scenario_overcommit, 6),
        risk_level=_classify_risk(scenario_overcommit),
    )

    return WhatIfResponse(current=current_metrics, scenario=scenario_metrics)
