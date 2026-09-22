"""Tests for the What-If Simulation endpoint.

Validates:
1. Endpoint accepts valid input and returns 200.
2. Response contains current and scenario metrics.
3. Scenario calculations are deterministic.
4. Changing capacity changes the hypothetical result.
5. Changing agent_count changes the hypothetical result.
6. What-If does NOT mutate actual resources.
7. What-If does NOT create or modify options.
8. Edge cases: zero agents, zero capacity, probability boundaries.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.store import store


@pytest.fixture(autouse=True)
def _clean_store():
    """Reset store before each test."""
    store.reset()
    yield
    store.reset()


client = TestClient(app)


# ────────────────────────────────────────────────────────────────────
# Helper
# ────────────────────────────────────────────────────────────────────

def _whatif(agent_count: int = 3, resource_capacity: int = 2, average_probability: float = 0.8):
    """Send a what-if request and return the response."""
    return client.post("/api/v1/simulation/what-if", json={
        "agent_count": agent_count,
        "resource_capacity": resource_capacity,
        "average_probability": average_probability,
    })


def _create_resource(name="gpu-1", capability="GPU_COMPUTE", total_capacity=2):
    """Create a resource via the API."""
    return client.post("/api/v1/resources", json={
        "name": name,
        "capability": capability,
        "total_capacity": total_capacity,
    })


def _create_option(agent_id="agent-1", capability="GPU_COMPUTE", probability=0.7):
    """Create an option via the API."""
    return client.post("/api/v1/options", json={
        "agent_id": agent_id,
        "capability": capability,
        "probability": probability,
        "expires_at": "2099-12-31T23:59:59Z",
    })


# ────────────────────────────────────────────────────────────────────
# Test: Endpoint accepts valid input
# ────────────────────────────────────────────────────────────────────

class TestWhatIfAcceptsValidInput:

    def test_returns_200(self):
        resp = _whatif()
        assert resp.status_code == 200

    def test_returns_json(self):
        resp = _whatif()
        data = resp.json()
        assert "current" in data
        assert "scenario" in data

    def test_rejects_negative_agent_count(self):
        resp = client.post("/api/v1/simulation/what-if", json={
            "agent_count": -1,
            "resource_capacity": 2,
            "average_probability": 0.5,
        })
        assert resp.status_code == 422

    def test_rejects_probability_above_one(self):
        resp = client.post("/api/v1/simulation/what-if", json={
            "agent_count": 3,
            "resource_capacity": 2,
            "average_probability": 1.5,
        })
        assert resp.status_code == 422

    def test_rejects_missing_fields(self):
        resp = client.post("/api/v1/simulation/what-if", json={})
        assert resp.status_code == 422


# ────────────────────────────────────────────────────────────────────
# Test: Response contains current and scenario metrics
# ────────────────────────────────────────────────────────────────────

class TestWhatIfResponseStructure:

    def test_current_has_required_fields(self):
        resp = _whatif()
        current = resp.json()["current"]
        assert "capacity" in current
        assert "expected_demand" in current
        assert "overcommit_probability" in current
        assert "risk_level" in current

    def test_scenario_has_required_fields(self):
        resp = _whatif()
        scenario = resp.json()["scenario"]
        assert "capacity" in scenario
        assert "agent_count" in scenario
        assert "expected_demand" in scenario
        assert "overcommit_probability" in scenario
        assert "risk_level" in scenario

    def test_risk_level_is_valid_enum(self):
        resp = _whatif()
        data = resp.json()
        valid_levels = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
        assert data["current"]["risk_level"] in valid_levels
        assert data["scenario"]["risk_level"] in valid_levels

    def test_current_reflects_real_state(self):
        """With resources and pending options, current should reflect them."""
        _create_resource("gpu-1", "GPU_COMPUTE", 2)
        _create_option("agent-1", "GPU_COMPUTE", 0.9)
        _create_option("agent-2", "GPU_COMPUTE", 0.8)

        resp = _whatif()
        current = resp.json()["current"]
        assert current["pending_options"] == 2
        assert current["capacity"] == 2
        assert current["expected_demand"] > 0


# ────────────────────────────────────────────────────────────────────
# Test: Scenario calculations are deterministic
# ────────────────────────────────────────────────────────────────────

class TestWhatIfDeterministic:

    def test_same_input_same_output(self):
        r1 = _whatif(5, 2, 0.7).json()["scenario"]
        r2 = _whatif(5, 2, 0.7).json()["scenario"]
        assert r1["expected_demand"] == r2["expected_demand"]
        assert r1["overcommit_probability"] == r2["overcommit_probability"]
        assert r1["risk_level"] == r2["risk_level"]

    def test_scenario_capacity_matches_input(self):
        resp = _whatif(3, 5, 0.5)
        assert resp.json()["scenario"]["capacity"] == 5

    def test_scenario_agent_count_matches_input(self):
        resp = _whatif(7, 2, 0.6)
        assert resp.json()["scenario"]["agent_count"] == 7


# ────────────────────────────────────────────────────────────────────
# Test: Changing capacity changes hypothetical result
# ────────────────────────────────────────────────────────────────────

class TestWhatIfCapacityEffect:

    def test_lower_capacity_higher_risk(self):
        low_cap = _whatif(5, 1, 0.8).json()["scenario"]
        high_cap = _whatif(5, 10, 0.8).json()["scenario"]
        assert low_cap["overcommit_probability"] >= high_cap["overcommit_probability"]

    def test_zero_capacity_maximum_risk(self):
        """With capacity 0 and agents demanding resources, overcommit should be high."""
        resp = _whatif(3, 0, 0.8)
        scenario = resp.json()["scenario"]
        # Any non-zero demand against 0 capacity = guaranteed overcommit
        assert scenario["overcommit_probability"] > 0.0


# ────────────────────────────────────────────────────────────────────
# Test: Changing agent_count changes hypothetical result
# ────────────────────────────────────────────────────────────────────

class TestWhatIfAgentCountEffect:

    def test_more_agents_higher_demand(self):
        few = _whatif(2, 3, 0.8).json()["scenario"]
        many = _whatif(8, 3, 0.8).json()["scenario"]
        assert many["expected_demand"] > few["expected_demand"]

    def test_more_agents_higher_risk(self):
        few = _whatif(1, 2, 0.8).json()["scenario"]
        many = _whatif(5, 2, 0.8).json()["scenario"]
        assert many["overcommit_probability"] >= few["overcommit_probability"]

    def test_zero_agents_zero_demand(self):
        resp = _whatif(0, 5, 0.8)
        scenario = resp.json()["scenario"]
        assert scenario["expected_demand"] == 0.0
        assert scenario["overcommit_probability"] == 0.0
        assert scenario["risk_level"] == "LOW"


# ────────────────────────────────────────────────────────────────────
# Test: What-If does NOT mutate state
# ────────────────────────────────────────────────────────────────────

class TestWhatIfNoMutation:

    def test_no_options_created(self):
        """Running what-if should NOT create any options in the store."""
        initial_options = len(store.options)
        _whatif(10, 2, 0.9)
        assert len(store.options) == initial_options

    def test_no_resources_modified(self):
        """Running what-if should NOT modify resources."""
        _create_resource("gpu-1", "GPU_COMPUTE", 5)
        resource_before = list(store.resources.values())[0]
        cap_before = resource_before.total_capacity

        _whatif(10, 1, 0.9)

        resource_after = list(store.resources.values())[0]
        assert resource_after.total_capacity == cap_before

    def test_no_allocations_created(self):
        """Running what-if should NOT create allocations."""
        initial_allocs = len(store.allocations)
        _whatif(10, 2, 0.9)
        assert len(store.allocations) == initial_allocs

    def test_no_events_logged(self):
        """Running what-if should NOT log any events."""
        initial_events = len(store.events)
        _whatif(10, 2, 0.9)
        assert len(store.events) == initial_events

    def test_existing_options_unchanged(self):
        """Existing options must not be modified by what-if."""
        _create_resource("gpu-1", "GPU_COMPUTE", 3)
        opt_resp = _create_option("agent-1", "GPU_COMPUTE", 0.7)
        opt_id = opt_resp.json()["id"]

        _whatif(20, 1, 0.99)

        option = store.options[opt_id]
        assert option.probability == 0.7
        assert option.status.value == "PENDING"


# ────────────────────────────────────────────────────────────────────
# Test: Edge cases
# ────────────────────────────────────────────────────────────────────

class TestWhatIfEdgeCases:

    def test_probability_zero(self):
        resp = _whatif(5, 2, 0.0)
        scenario = resp.json()["scenario"]
        assert scenario["expected_demand"] == 0.0
        assert scenario["overcommit_probability"] == 0.0
        assert scenario["risk_level"] == "LOW"

    def test_probability_one(self):
        """All agents certain to exercise — demand equals agent count."""
        resp = _whatif(5, 2, 1.0)
        scenario = resp.json()["scenario"]
        assert scenario["expected_demand"] == 5.0
        # 5 agents, capacity 2 → guaranteed overcommit
        assert scenario["overcommit_probability"] == 1.0
        assert scenario["risk_level"] == "CRITICAL"

    def test_empty_system_current(self):
        """With no resources, current should show zero capacity."""
        resp = _whatif(3, 2, 0.5)
        current = resp.json()["current"]
        assert current["capacity"] == 0
        assert current["pending_options"] == 0

    def test_high_agent_count_within_limit(self):
        """50 agents (max) should still compute."""
        resp = _whatif(50, 10, 0.5)
        assert resp.status_code == 200

    def test_agent_count_above_limit_rejected(self):
        """Above 50 agents should be rejected (validation)."""
        resp = client.post("/api/v1/simulation/what-if", json={
            "agent_count": 51,
            "resource_capacity": 2,
            "average_probability": 0.5,
        })
        assert resp.status_code == 422
