"""Risk engine — probabilistic over-commitment analysis.

For each capability, computes the probability that simultaneous exercise
of pending options would exceed available capacity.

Algorithm:  Exact 2^n subset enumeration.
Assumption: Each option is exercised independently (no inter-agent correlation).
Limitation: Practical for n <= ~20 options per capability (sufficient for hackathon).
"""

from __future__ import annotations

from datetime import datetime, timezone
from itertools import product

from backend.models.enums import CapabilityType, RiskLevel
from backend.models.risk import RiskReport, SystemRiskSummary
from backend.store import store


def _classify_risk(p: float) -> RiskLevel:
    """Map overcommit probability to a qualitative risk level."""
    if p < 0.10:
        return RiskLevel.LOW
    if p < 0.30:
        return RiskLevel.MEDIUM
    if p < 0.60:
        return RiskLevel.HIGH
    return RiskLevel.CRITICAL


def _compute_overcommit_probability(
    available_capacity: int,
    options: list[tuple[float, int]],
) -> float:
    """Exact enumeration of all 2^n subsets.

    Args:
        available_capacity: Units currently available.
        options: List of (probability, amount) for each pending option.

    Returns:
        Probability that total simultaneous demand exceeds available capacity.
    """
    n = len(options)
    if n == 0 or available_capacity < 0:
        return 0.0

    overcommit_prob = 0.0

    # Enumerate all 2^n combinations: each option is exercised (1) or not (0)
    for bits in product((0, 1), repeat=n):
        subset_prob = 1.0
        demand = 0
        for i, bit in enumerate(bits):
            p_i, a_i = options[i]
            if bit:
                subset_prob *= p_i
                demand += a_i
            else:
                subset_prob *= 1.0 - p_i
        if demand > available_capacity:
            overcommit_prob += subset_prob

    return overcommit_prob


def _compute_expected_demand(options: list[tuple[float, int]]) -> float:
    """E[demand] = sum(p_i * a_i)."""
    return sum(p * a for p, a in options)


def compute_risk_for_capability(capability: CapabilityType) -> RiskReport | None:
    """Compute risk for a single capability across all resources providing it.

    Returns None if no resources exist for this capability.
    """
    resources = store.resources_by_capability(capability)
    if not resources:
        return None

    total_cap = sum(r.total_capacity for r in resources)
    alloc_cap = sum(r.allocated_capacity for r in resources)
    avail_cap = total_cap - alloc_cap
    resource_ids = [r.id for r in resources]

    pending = store.pending_options_by_capability(capability)
    options_data = [(o.probability, o.amount) for o in pending]

    total_demand = sum(o.amount for o in pending)
    expected = _compute_expected_demand(options_data)
    overcommit_p = _compute_overcommit_probability(avail_cap, options_data)

    return RiskReport(
        capability=capability,
        resource_ids=resource_ids,
        total_capacity=total_cap,
        allocated_capacity=alloc_cap,
        available_capacity=avail_cap,
        pending_options_count=len(pending),
        total_pending_demand=total_demand,
        expected_demand=round(expected, 4),
        overcommit_probability=round(overcommit_p, 6),
        risk_level=_classify_risk(overcommit_p),
    )


def compute_system_risk() -> SystemRiskSummary:
    """Compute risk across all capabilities with registered resources."""
    # Collect unique capabilities that have resources
    capabilities = {r.capability for r in store.resources.values()}

    reports: list[RiskReport] = []
    for cap in sorted(capabilities, key=lambda c: c.value):
        report = compute_risk_for_capability(cap)
        if report is not None:
            reports.append(report)

    highest = RiskLevel.LOW
    level_order = [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
    for r in reports:
        if level_order.index(r.risk_level) > level_order.index(highest):
            highest = r.risk_level

    return SystemRiskSummary(
        timestamp=datetime.now(timezone.utc),
        capability_risks=reports,
        highest_risk_level=highest,
        total_pending_options=len(store.pending_options()),
        total_active_allocations=len(store.active_allocations()),
    )
