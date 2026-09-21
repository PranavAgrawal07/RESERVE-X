import sys
from pathlib import Path

# Ensure the simulation directory is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from agents import Agent, WorkflowStep
from predictor import Predictor
from resources import (
    RESOURCE_TO_CAPABILITY_MAP,
    is_supported_resource,
    map_resource_to_capability,
)
from reservex_client import MockReserveXClient, ReserveXClient
from simulator import MultiAgentSimulator, create_default_agents


def test_phase_1_basic_agent():
    print("=== Phase 1: Basic Agent Model Test ===")
    agent = Agent(
        agent_id="agent-001",
        agent_type="coding",
        current_task="writing_code",
        workflow_step="implementation",
        status="busy",
    )
    assert agent.agent_id == "agent-001"
    assert agent.agent_type == "coding"
    assert agent.current_task == "writing_code"
    assert agent.workflow_step == "implementation"
    assert agent.status == "busy"

    agent.update_task("running_unit_tests", workflow_step="testing", status="testing")
    agent.update_workflow_step("code_review")
    agent.update_status("reviewing")

    assert agent.current_task == "running_unit_tests"
    assert agent.workflow_step == "code_review"
    assert agent.status == "reviewing"
    print("Phase 1 assertions passed.\n")


def test_phase_2_workflow_simulation():
    print("=== Phase 2: Agent Workflow Simulation Test ===")

    agent = Agent(agent_id="agent-001", agent_type="coding")

    workflow = [
        WorkflowStep(name="write_code", required_resource="terminal", duration=2),
        WorkflowStep(name="run_tests", required_resource="testing_environment", duration=1),
        WorkflowStep(name="debug", required_resource="LLM", duration=3),
        WorkflowStep(name="run_tests", required_resource="testing_environment", duration=1),
        WorkflowStep(name="deploy", required_resource="deployment_environment", duration=2),
    ]
    agent.set_workflow(workflow)

    print("\nPredefined Coding Workflow:")
    for idx, step in enumerate(workflow, start=1):
        print(f"  Step {idx}: {step.name} -> {step.required_resource} ({step.duration} ticks)")

    assert not agent.is_complete(), "Workflow should not be complete initially"
    initial_step = agent.get_current_step()
    upcoming_step = agent.get_upcoming_step()
    print(f"\nInitial State: Current Step = '{initial_step.name}' (needs: {initial_step.required_resource}) | Upcoming = '{upcoming_step.name}'")
    assert initial_step.name == "write_code"
    assert upcoming_step.name == "run_tests"

    transition = 1
    while not agent.is_complete():
        agent.advance_step()
        current = agent.get_current_step()
        upcoming = agent.get_upcoming_step()
        curr_desc = f"'{current.name}' (needs: {current.required_resource})" if current else "None (Workflow Completed)"
        up_desc = f"'{upcoming.name}'" if upcoming else "None"
        print(f"Transition {transition}: Current Step = {curr_desc} | Upcoming Step = {up_desc}")
        transition += 1

    assert agent.is_complete() is True, "Workflow should be marked complete"
    assert agent.get_current_step() is None, "Current step should be None after completion"
    assert agent.get_upcoming_step() is None, "Upcoming step should be None after completion"
    assert agent.status == "completed", "Agent status should be 'completed'"

    print("\nPHASE 2 TEST PASSED\n")


def test_phase_3_prediction():
    print("=== Phase 3: Future Dependency Prediction Test ===")
    historical_data = {
        "LLM": 0.8,
        "GPU": 0.4,
        "testing_environment": 0.9,
        "deployment_environment": 0.4,
    }

    predictor = Predictor(historical_data=historical_data)

    workflow = [
        WorkflowStep(name="write_code", required_resource="terminal", duration=2),
        WorkflowStep(name="run_tests", required_resource="testing_environment", duration=1),
        WorkflowStep(name="debug", required_resource="LLM", duration=3),
        WorkflowStep(name="run_tests", required_resource="testing_environment", duration=1),
        WorkflowStep(name="deploy", required_resource="deployment_environment", duration=2),
    ]

    agent = Agent(agent_id="agent-001", agent_type="coding")
    agent.set_workflow(workflow)

    print("\n=== RESERVE-X FUTURE DEPENDENCY PREDICTION ===")
    print(f"\nAgent: {agent.agent_id}")
    print(f"Current step: {agent.current_step.name}\n")
    print("Predicted future resource needs:\n")

    preds_step1 = predictor.predict(agent)
    for resource, prob in preds_step1.items():
        print(f"{resource:<24} {prob:.2f}")

    assert "testing_environment" in preds_step1
    assert "LLM" in preds_step1
    assert "deployment_environment" in preds_step1
    assert "terminal" in preds_step1
    for res, prob in preds_step1.items():
        assert 0.0 <= prob <= 1.0

    assert "GPU" not in preds_step1

    agent.advance_step()
    agent.advance_step()
    assert agent.current_step.name == "debug"

    print("\n--- Advanced to 'debug' step ---")
    print(f"Agent: {agent.agent_id}")
    print(f"Current step: {agent.current_step.name}\n")
    print("Predicted future resource needs:\n")

    preds_debug = predictor.predict(agent)
    for resource, prob in preds_debug.items():
        print(f"{resource:<24} {prob:.2f}")

    assert preds_debug["LLM"] > preds_step1["LLM"]
    assert "terminal" not in preds_debug or preds_debug.get("terminal", 0.0) == 0.0

    while not agent.is_complete():
        agent.advance_step()

    assert agent.is_complete() is True
    preds_complete = predictor.predict(agent)
    assert preds_complete == {}

    agent_hist_test = Agent(agent_id="agent-002", agent_type="coding")
    agent_hist_test.set_workflow(workflow)

    pred_a = predictor.predict(agent_hist_test, historical_data={"LLM": 0.1})
    pred_b = predictor.predict(agent_hist_test, historical_data={"LLM": 0.9})

    assert pred_b["LLM"] > pred_a["LLM"]

    print("\nPHASE 3 TEST PASSED\n")


def test_phase_4_multi_agent_simulation():
    agents = create_default_agents()
    agent_name_map = {agent.agent_id: f"{agent.agent_type} Agent" for agent in agents}
    sim = MultiAgentSimulator(agents=agents)

    print("=== RESERVE-X MULTI-AGENT SIMULATION ===\n")
    print("Active Agents:\n")
    for agent in sim.active_agents:
        print(f"[{agent.agent_id}] {agent.agent_type}")
        print(f"Current: {agent.current_step.name}\n")

    def print_resource_demand(demand: dict[str, dict[str, float]], title: str):
        print(f"=== {title} ===\n")
        priority_order = [
            "LLM",
            "testing_environment",
            "terminal",
            "database",
            "GPU",
            "security_scanner",
            "search_tool",
            "deployment_environment",
        ]
        sorted_resources = sorted(
            demand.keys(),
            key=lambda r: priority_order.index(r) if r in priority_order else 99,
        )
        for res in sorted_resources:
            print(res)
            for agent_id, prob in demand[res].items():
                name = agent_name_map.get(agent_id, agent_id)
                print(f"  {name:<18} {prob:.2f}")
            print()

    demand_tick0 = sim.get_predicted_resource_demand()
    print_resource_demand(demand_tick0, "PREDICTED RESOURCE DEMAND")

    # TEST 1: Verify all 5 agents exist, have workflows, and start at correct step
    assert len(sim.agents) == 5, "Expected 5 registered agents"
    expected_first_steps = {
        "agent-001": "write_code",
        "agent-002": "search_web",
        "agent-003": "prepare_tests",
        "agent-004": "scan_code",
        "agent-005": "load_data",
    }
    for agent_id, step_name in expected_first_steps.items():
        agent = sim.get_agent(agent_id)
        assert agent is not None, f"Agent {agent_id} should exist"
        assert len(agent.workflow) > 0, f"Agent {agent_id} should have a workflow"
        assert agent.current_step.name == step_name, (
            f"Agent {agent_id} should start at {step_name}, got {agent.current_step.name}"
        )

    # TEST 2: Advance simulator by one tick
    print("--- Advancing simulation by 1 tick ---\n")
    sim.tick()
    assert sim.current_tick == 1, "Simulation tick should increment to 1"

    expected_second_steps = {
        "agent-001": "run_tests",
        "agent-002": "analyze_sources",
        "agent-003": "run_tests",
        "agent-004": "analyze_vulnerability",
        "agent-005": "query_database",
    }
    for agent_id, step_name in expected_second_steps.items():
        agent = sim.get_agent(agent_id)
        assert agent.current_step.name == step_name, (
            f"Agent {agent_id} should advance to {step_name}, got {agent.current_step.name}"
        )

    demand_tick1 = sim.get_predicted_resource_demand()
    print_resource_demand(demand_tick1, "PREDICTED RESOURCE DEMAND (TICK 1)")

    # TEST 3: Verify predictor outputs for all active agents
    agent_predictions = sim.get_agent_predictions()
    assert len(agent_predictions) == len(sim.active_agents), "All active agents must produce predictions"
    for agent_id, preds in agent_predictions.items():
        assert len(preds) > 0, f"Agent {agent_id} should have predicted future requirements"
        for resource, prob in preds.items():
            assert 0.0 <= prob <= 1.0, f"Probability for {resource} on {agent_id} must be in [0, 1], got {prob}"

    # TEST 4: Verify resource competition & overlapping demands
    assert "LLM" in demand_tick0, "LLM should be in resource demand"
    assert "testing_environment" in demand_tick0, "testing_environment should be in resource demand"
    assert len(demand_tick0["LLM"]) >= 3, (
        f"Multiple agents should demand LLM, got {len(demand_tick0['LLM'])}"
    )
    assert len(demand_tick0["testing_environment"]) >= 2, (
        f"Multiple agents should demand testing_environment, got {len(demand_tick0['testing_environment'])}"
    )

    # TEST 5: Advance simulation several ticks until agents complete independently
    sim.tick()  # tick 2
    sim.tick()  # tick 3
    sim.tick()  # tick 4

    coding_agent = sim.get_agent("agent-001")
    assert not coding_agent.is_complete(), "Coding agent should still be active at tick 4"
    assert coding_agent.current_step.name == "deploy"

    for aid in ["agent-002", "agent-003", "agent-004", "agent-005"]:
        assert sim.get_agent(aid).is_complete(), f"Agent {aid} should be completed at tick 4"

    demand_tick4 = sim.get_predicted_resource_demand()
    for res, agent_probs in demand_tick4.items():
        for aid in agent_probs:
            assert aid == "agent-001", f"Only active agent-001 should be in demand, found {aid}"

    sim.tick()  # tick 5
    assert coding_agent.is_complete(), "Coding agent should be complete at tick 5"
    assert len(sim.active_agents) == 0, "All agents should be completed"
    assert sim.get_predicted_resource_demand() == {}, "Demand must be empty when all agents complete"

    print("PHASE 4 TEST PASSED\n")


def test_phase_5_reservex_integration():
    print("=== RESERVE-X INTEGRATION TEST ===\n")

    # 1. Initialize fresh multi-agent simulation
    agents = create_default_agents()
    sim = MultiAgentSimulator(agents=agents)
    mock_client = MockReserveXClient()
    expires_at = "2026-09-21T20:00:00Z"

    # Print required human-readable integration mapping
    for agent in sim.active_agents:
        preds = sim.predictor.predict(agent)
        for resource, prob in preds.items():
            if prob > 0.0:
                capability = map_resource_to_capability(resource)
                print(f"Agent: {agent.agent_id}")
                print(f"Resource: {resource}")
                print(f"Capability: {capability}")
                print(f"Probability: {prob:.2f}\n")

    # 2. Submit predictions as conditional ResourceOptions
    created_options = sim.submit_predictions(mock_client, expires_at=expires_at)
    print("Options successfully prepared.\n")

    # --- VERIFICATION 1: Options count & predictions generation ---
    assert len(created_options) > 0, "Options should be generated from predictions"
    assert len(mock_client.options) == len(created_options), "Mock client must store all created options"

    # --- VERIFICATION 2 & 3: Correct capabilities and payloads constructed ---
    for opt in created_options:
        assert "option_id" in opt
        assert "agent_id" in opt and opt["agent_id"].startswith("agent-")
        assert "capability" in opt and opt["capability"] in RESOURCE_TO_CAPABILITY_MAP.values()
        assert "probability" in opt and 0.0 <= opt["probability"] <= 1.0
        assert opt["expires_at"] == expires_at
        # VERIFICATION 6: No option is exercised during submission
        assert opt["status"] == "PENDING", "Created options must remain in PENDING status"

    assert len(mock_client.exercised_options) == 0, "No option should be exercised during creation"

    # --- VERIFICATION 4 & 5: Coding, Research, and Testing agents create options with preserved probabilities ---
    coding_opts = [o for o in created_options if o["agent_id"] == "agent-001"]
    research_opts = [o for o in created_options if o["agent_id"] == "agent-002"]
    testing_opts = [o for o in created_options if o["agent_id"] == "agent-003"]

    assert len(coding_opts) >= 4, "Coding Agent should create options for its workflow predictions"
    assert len(research_opts) >= 2, "Research Agent should create options for its workflow predictions"
    assert len(testing_opts) >= 3, "Testing Agent should create options for its workflow predictions"

    # Check shared LLM_INFERENCE capability has separate options for different agents
    llm_opts = [o for o in created_options if o["capability"] == "LLM_INFERENCE"]
    llm_agent_ids = {o["agent_id"] for o in llm_opts}
    assert "agent-001" in llm_agent_ids, "Coding Agent should have LLM_INFERENCE option"
    assert "agent-002" in llm_agent_ids, "Research Agent should have LLM_INFERENCE option"
    assert "agent-003" in llm_agent_ids, "Testing Agent should have LLM_INFERENCE option"

    # Check shared TESTING capability has separate options for different agents
    testing_cap_opts = [o for o in created_options if o["capability"] == "TESTING"]
    testing_agent_ids = {o["agent_id"] for o in testing_cap_opts}
    assert "agent-001" in testing_agent_ids, "Coding Agent should have TESTING capability option"
    assert "agent-003" in testing_agent_ids, "Testing Agent should have TESTING capability option"

    # --- VERIFICATION 7: Unsupported/unknown resources handled safely ---
    try:
        map_resource_to_capability("UNKNOWN_QUANTUM_COMPUTE")
        assert False, "Should raise ValueError on unknown resource"
    except ValueError as e:
        assert "Unknown or unsupported resource" in str(e)

    assert not is_supported_resource("UNKNOWN_TOOL")
    assert is_supported_resource("LLM")
    assert is_supported_resource("GPU")

    # --- VERIFICATION 8: Risk retrieval ---
    risk_response = sim.get_risk(mock_client)
    assert "risk" in risk_response
    print("=== RESERVE-X RISK ===\n")
    for cap, info in risk_response["risk"].items():
        print(cap)
        print(f"Total predicted demand: {info['total_probability']:.2f}")
        print(f"Risk: {info['risk_level']}\n")

    # Optional live backend check (gracefully skips if offline)
    _check_live_backend_if_available()

    print("PHASE 5 TEST PASSED")


def _check_live_backend_if_available(base_url: str = "http://localhost:8000") -> None:
    """
    Attempts a live call against RESERVE-X if a local instance is running.
    Does not fail test suite if backend is unavailable.
    """
    client = ReserveXClient(base_url=base_url, timeout=1.0)
    try:
        risk = client.get_risk()
        print(f"[LIVE BACKEND DETECTED] Connected to {base_url}. Risk response: {risk}")
    except Exception:
        # Expected when backend is not running during standalone simulation tests
        pass


if __name__ == "__main__":
    test_phase_1_basic_agent()
    test_phase_2_workflow_simulation()
    test_phase_3_prediction()
    test_phase_4_multi_agent_simulation()
    test_phase_5_reservex_integration()
