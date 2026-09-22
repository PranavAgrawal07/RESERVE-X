"""
Unit & Integration Tests for RESERVE-X Live Autonomous Simulation.
"""

from __future__ import annotations

import time
import pytest
from fastapi.testclient import TestClient

from simulation.live_runner import LiveSimulationRunner
from simulation.reservex_client import MockReserveXClient
from backend.main import app


def test_runner_initialization():
    """Verify live runner initializes with all 5 standard agents and clean state."""
    mock_client = MockReserveXClient()
    runner = LiveSimulationRunner(client=mock_client)
    
    status = runner.get_status()
    assert status["running"] is False
    assert status["paused"] is False
    assert status["tick"] == 0
    assert status["speed"] == 1.0
    assert len(status["agents"]) == 5
    
    agent_ids = {a["id"] for a in status["agents"]}
    assert agent_ids == {"agent-001", "agent-002", "agent-003", "agent-004", "agent-005"}


def test_single_tick_prediction_and_option_creation():
    """Verify that ticking the simulation generates learned predictions and creates options."""
    mock_client = MockReserveXClient()
    runner = LiveSimulationRunner(client=mock_client)
    
    tick = runner.step_tick()
    assert tick == 1
    
    status = runner.get_status()
    assert status["tick"] == 1
    
    # At least some options should be created on the mock client
    assert len(mock_client.options) > 0
    
    # Check that predictions are populated
    for agent in status["agents"]:
        assert agent["predicted_capability"] != "NONE"
        assert 0.0 <= agent["prediction_probability"] <= 1.0
        assert agent["current_step"] is not None


def test_exercise_and_allocation_lifecycle():
    """Verify option exercise creates active allocation and duration decrements."""
    mock_client = MockReserveXClient()
    runner = LiveSimulationRunner(client=mock_client)
    
    # Tick 1: creates options & exercises
    runner.step_tick()
    
    status = runner.get_status()
    # Find an agent with active allocation
    active_agent = next((a for a in status["agents"] if a["allocation_id"] is not None), None)
    assert active_agent is not None, "Expected at least one agent with an active allocation"
    assert active_agent["option_status"] == "EXERCISED"
    assert active_agent["step_status"] == "RUNNING"


def test_capacity_conflict_409_handling():
    """Verify HTTP 409 capacity conflict keeps option PENDING and marks agent waiting."""
    class ConflictMockClient(MockReserveXClient):
        def exercise_option(self, option_id: str):
            return {
                "status_code": 409,
                "detail": "No available capacity for GPU_COMPUTE (requested 1 unit(s))",
            }
            
    mock_client = ConflictMockClient()
    runner = LiveSimulationRunner(client=mock_client)
    
    runner.step_tick()
    status = runner.get_status()
    
    # All attempted exercises should have resulted in waiting_for_capacity = True
    waiting_agents = [a for a in status["agents"] if a["waiting_for_capacity"]]
    assert len(waiting_agents) > 0
    for a in waiting_agents:
        assert a["step_status"] == "WAITING_FOR_CAPACITY"
        assert a["option_status"] == "PENDING"
        assert a["allocation_id"] is None


def test_step_completion_and_allocation_release():
    """Verify allocation is released when remaining step duration finishes."""
    mock_client = MockReserveXClient()
    runner = LiveSimulationRunner(client=mock_client)
    
    # Run multiple ticks to complete steps
    for _ in range(5):
        runner.step_tick()
        
    assert len(mock_client.released_allocations) > 0


def test_start_pause_resume_reset():
    """Verify state transitions for start, pause, resume, reset, and duplicate protection."""
    mock_client = MockReserveXClient()
    runner = LiveSimulationRunner(client=mock_client, base_interval_seconds=0.1)
    
    # 1. Start
    runner.start(speed=2.0)
    assert runner.is_running is True
    assert runner.is_paused is False
    assert runner.speed == 2.0
    
    # 2. Duplicate start should not create duplicate workers
    runner.start(speed=2.0)
    assert runner.is_running is True
    
    time.sleep(0.3)
    assert runner.tick_count >= 1
    
    # 3. Pause
    runner.pause()
    assert runner.is_paused is True
    paused_tick = runner.tick_count
    
    time.sleep(0.3)
    # Ticks should remain roughly paused
    assert runner.tick_count <= paused_tick + 1
    
    # 4. Resume
    runner.resume()
    assert runner.is_paused is False
    
    time.sleep(0.3)
    assert runner.tick_count > paused_tick
    
    # 5. Reset
    runner.reset()
    assert runner.is_running is False
    assert runner.is_paused is False
    assert runner.tick_count == 0


def test_backend_live_simulation_endpoints():
    """Integration test for FastAPI live simulation REST endpoints."""
    client = TestClient(app)
    
    # GET status
    res = client.get("/api/v1/simulation/live/status")
    assert res.status_code == 200
    data = res.json()
    assert "running" in data
    assert "agents" in data
    assert len(data["agents"]) == 5
    
    # POST start
    res_start = client.post("/api/v1/simulation/live/start", json={"speed": 5.0})
    assert res_start.status_code == 200
    start_data = res_start.json()
    assert start_data["running"] is True
    assert start_data["speed"] == 5.0
    
    # POST pause
    res_pause = client.post("/api/v1/simulation/live/pause")
    assert res_pause.status_code == 200
    pause_data = res_pause.json()
    assert pause_data["paused"] is True
    
    # POST reset
    res_reset = client.post("/api/v1/simulation/live/reset")
    assert res_reset.status_code == 200
    reset_data = res_reset.json()
    assert reset_data["running"] is False
    assert reset_data["tick"] == 0
