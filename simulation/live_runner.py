"""
Live Autonomous Simulation Runner for RESERVE-X.

Orchestrates the 5 standard agents continuously driving workflows,
calling LearnedPredictor for next-capability predictions, creating conditional
options, exercising options when reaching required steps, handling HTTP 409 contention,
holding allocations for step durations, and releasing resources back to the pool.
"""

from __future__ import annotations

import logging
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Any

try:
    from .agents import Agent, WorkflowStep
    from .learned_predictor import LearnedPredictor
    from .reservex_client import ReserveXClient
    from .resources import map_resource_to_capability
    from .simulator import create_default_agents
except ImportError:
    from agents import Agent, WorkflowStep
    from learned_predictor import LearnedPredictor
    from reservex_client import ReserveXClient
    from resources import map_resource_to_capability
    from simulator import create_default_agents

logger = logging.getLogger(__name__)


class AgentLiveState:
    """Tracks live autonomous simulation state for a single agent."""

    def __init__(self, agent: Agent):
        self.agent = agent
        self.agent_id = agent.agent_id
        self.agent_type = agent.agent_type
        self.name = f"{agent.agent_type} Agent"
        
        # Current execution state
        self.current_step_name: str = "init"
        self.current_capability: str = "NONE"
        self.predicted_capability: str = "NONE"
        self.prediction_probability: float = 0.0
        
        # Active option / allocation bindings
        self.option_id: str | None = None
        self.option_status: str = "NONE"
        self.allocation_id: str | None = None
        
        # Duration & Contention tracking
        self.remaining_duration: int = 1
        self.waiting_for_capacity: bool = False
        self.step_status: str = "IDLE"  # IDLE | PREDICTING | RUNNING | WAITING_FOR_CAPACITY | COMPLETED

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.agent_id,
            "name": self.name,
            "agent_type": self.agent_type,
            "current_step": self.current_step_name,
            "current_capability": self.current_capability,
            "predicted_capability": self.predicted_capability,
            "prediction_probability": round(self.prediction_probability, 4),
            "option_id": self.option_id,
            "option_status": self.option_status,
            "allocation_id": self.allocation_id,
            "remaining_duration": self.remaining_duration,
            "waiting_for_capacity": self.waiting_for_capacity,
            "step_status": self.step_status,
        }


class LiveSimulationRunner:
    """
    Autonomous Live Simulation Runner for RESERVE-X.
    Coordinates the 5 agents, learned predictions, and real backend lifecycle.
    """

    def __init__(
        self,
        client: ReserveXClient | Any | None = None,
        predictor: LearnedPredictor | None = None,
        base_interval_seconds: float = 2.0,
    ):
        self.client = client or ReserveXClient()
        self.predictor = predictor or LearnedPredictor()
        self.base_interval_seconds = base_interval_seconds
        self.speed: float = 1.0
        
        self.tick_count: int = 0
        self.is_running: bool = False
        self.is_paused: bool = False
        
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._lock = threading.Lock()
        
        self.agent_states: dict[str, AgentLiveState] = {}
        self._init_agents()

    def _init_agents(self) -> None:
        """Instantiate the 5 standard agents and their tracking states."""
        default_agents = create_default_agents()
        self.agent_states = {}
        for agent in default_agents:
            state = AgentLiveState(agent)
            step = agent.get_current_step()
            if step:
                state.current_step_name = step.name
                try:
                    state.current_capability = map_resource_to_capability(step.required_resource)
                except ValueError:
                    state.current_capability = step.required_resource
                state.remaining_duration = step.duration
                state.step_status = "IDLE"
            self.agent_states[agent.agent_id] = state

    def start(self, speed: float = 1.0) -> None:
        """Start or resume the autonomous simulation loop."""
        with self._lock:
            if speed > 0:
                self.speed = float(speed)
            
            if self.is_running and self.is_paused:
                self.is_paused = False
                self._pause_event.clear()
                logger.info("Resumed live simulation.")
                return

            if self.is_running:
                logger.info("Simulation is already running.")
                return

            self.is_running = True
            self.is_paused = False
            self._stop_event.clear()
            self._pause_event.clear()
            
            self._thread = threading.Thread(target=self._run_loop, daemon=True, name="ReserveXLiveSim")
            self._thread.start()
            logger.info("Live simulation started.")

    def pause(self) -> None:
        """Pause the autonomous simulation loop without destroying state."""
        with self._lock:
            if not self.is_running or self.is_paused:
                return
            self.is_paused = True
            self._pause_event.set()
            logger.info("Live simulation paused.")

    def resume(self, speed: float | None = None) -> None:
        """Resume execution."""
        self.start(speed=speed or self.speed)

    def reset(self) -> None:
        """Stop the runner, release active allocations, and reset agent workflows."""
        with self._lock:
            self.is_running = False
            self.is_paused = False
            self._stop_event.set()
            self._pause_event.clear()

        if self._thread and self._thread.is_alive() and threading.current_thread() != self._thread:
            self._thread.join(timeout=2.0)

        with self._lock:
            # Release any held allocations
            for state in self.agent_states.values():
                if state.allocation_id:
                    try:
                        self.client.release_allocation(state.allocation_id)
                    except Exception as e:
                        logger.debug("Failed to release allocation %s on reset: %s", state.allocation_id, e)
            
            self.tick_count = 0
            self._init_agents()
            logger.info("Live simulation reset.")

    def set_speed(self, speed: float) -> None:
        """Update simulation speed multiplier (e.g. 1.0, 2.0, 5.0)."""
        with self._lock:
            if speed > 0:
                self.speed = float(speed)

    def _run_loop(self) -> None:
        """Background worker thread execution loop."""
        while not self._stop_event.is_set():
            if self._pause_event.is_set():
                time.sleep(0.2)
                continue

            try:
                self.step_tick()
            except Exception as e:
                logger.error("Error during simulation tick: %s", e, exc_info=True)

            sleep_duration = max(0.1, self.base_interval_seconds / self.speed)
            # Sleep in small increments to respond quickly to stop/pause events
            elapsed = 0.0
            while elapsed < sleep_duration and not self._stop_event.is_set() and not self._pause_event.is_set():
                time.sleep(0.1)
                elapsed += 0.1

    def step_tick(self) -> int:
        """
        Execute a single simulation tick across all 5 agents.
        Can be called by background thread or synchronously in tests.
        """
        with self._lock:
            self.tick_count += 1
            now_utc = datetime.now(timezone.utc)
            expires_at = (now_utc + timedelta(minutes=15)).strftime("%Y-%m-%dT%H:%M:%SZ")

            for agent_id, state in self.agent_states.items():
                try:
                    self._process_agent_tick(state, expires_at)
                except Exception as e:
                    logger.warning("Error processing agent %s in tick %d: %s", agent_id, self.tick_count, e)

            return self.tick_count

    def _process_agent_tick(self, state: AgentLiveState, expires_at: str) -> None:
        """Process simulation cycle for a single agent."""
        agent = state.agent

        # 1. If workflow is completed, loop/restart for continuous demo
        if agent.is_complete():
            default_agents = create_default_agents()
            fresh = next((a for a in default_agents if a.agent_id == state.agent_id), None)
            if fresh:
                agent.set_workflow(fresh.workflow)
                state.option_id = None
                state.option_status = "NONE"
                state.allocation_id = None
                state.waiting_for_capacity = False

        step = agent.get_current_step()
        if not step:
            return

        state.current_step_name = step.name
        try:
            current_cap = map_resource_to_capability(step.required_resource)
        except ValueError:
            current_cap = step.required_resource
        state.current_capability = current_cap

        # 2. Predict next capability using LearnedPredictor
        try:
            pred = self.predictor.predict(
                agent_type=state.agent_type,
                step_name=step.name,
                current_capability=current_cap,
            )
            state.predicted_capability = str(pred.get("capability", "NONE"))
            state.prediction_probability = float(pred.get("probability", 0.0))
        except Exception:
            state.predicted_capability = "NONE"
            state.prediction_probability = 0.5

        # 3. If agent has no allocation and no pending option, create conditional option for current/predicted need
        target_capability = current_cap
        if not state.allocation_id and not state.option_id:
            try:
                # Create conditional option on real backend
                opt_res = self.client.create_option(
                    agent_id=state.agent_id,
                    capability=target_capability,
                    probability=max(0.5, state.prediction_probability),
                    expires_at=expires_at,
                )
                if isinstance(opt_res, dict) and "id" in opt_res:
                    state.option_id = opt_res["id"]
                    state.option_status = opt_res.get("status", "PENDING")
                    state.step_status = "PREDICTING"
            except Exception as e:
                logger.debug("Failed to create option for %s: %s", state.agent_id, e)

        # 4. If agent does NOT hold an active allocation, attempt to exercise option
        if not state.allocation_id:
            if state.option_id and state.option_status == "PENDING":
                try:
                    exercise_res = self.client.exercise_option(state.option_id)
                    if isinstance(exercise_res, dict):
                        # Check for 409 / capacity failure
                        if exercise_res.get("status_code") == 409 or "detail" in exercise_res:
                            # Contention! Option remains PENDING
                            state.waiting_for_capacity = True
                            state.step_status = "WAITING_FOR_CAPACITY"
                            state.option_status = "PENDING"
                        elif "id" in exercise_res or "allocation_id" in exercise_res:
                            # Exercise succeeded!
                            state.allocation_id = exercise_res.get("id") or exercise_res.get("allocation_id")
                            state.option_status = "EXERCISED"
                            state.waiting_for_capacity = False
                            state.step_status = "RUNNING"
                            state.remaining_duration = step.duration
                except Exception as e:
                    logger.debug("Exercise error for agent %s: %s", state.agent_id, e)
                    state.waiting_for_capacity = True
                    state.step_status = "WAITING_FOR_CAPACITY"

        # 5. If agent holds an active allocation, execute step & count down duration
        if state.allocation_id:
            state.step_status = "RUNNING"
            state.waiting_for_capacity = False
            state.remaining_duration -= 1

            # When step duration finishes, release allocation and advance workflow
            if state.remaining_duration <= 0:
                alloc_to_release = state.allocation_id
                state.allocation_id = None
                state.option_id = None
                state.option_status = "NONE"

                try:
                    self.client.release_allocation(alloc_to_release)
                except Exception as e:
                    logger.debug("Failed to release allocation %s: %s", alloc_to_release, e)

                # Advance to next workflow step
                next_step = agent.advance_step()
                if next_step:
                    state.current_step_name = next_step.name
                    try:
                        state.current_capability = map_resource_to_capability(next_step.required_resource)
                    except ValueError:
                        state.current_capability = next_step.required_resource
                    state.remaining_duration = next_step.duration
                    state.step_status = "IDLE"
                else:
                    state.step_status = "COMPLETED"

    def get_status(self) -> dict[str, Any]:
        """Return structured real-time status of the live simulation."""
        with self._lock:
            return {
                "running": self.is_running,
                "paused": self.is_paused,
                "tick": self.tick_count,
                "speed": self.speed,
                "agents": [state.to_dict() for state in self.agent_states.values()],
            }


# Singleton live runner instance for backend process
_global_live_runner: LiveSimulationRunner | None = None
_runner_lock = threading.Lock()


def get_live_runner(client: ReserveXClient | Any | None = None) -> LiveSimulationRunner:
    """Retrieve or initialize the global singleton live simulation runner."""
    global _global_live_runner
    with _runner_lock:
        if _global_live_runner is None:
            _global_live_runner = LiveSimulationRunner(client=client)
        return _global_live_runner
