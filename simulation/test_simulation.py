import sys
from pathlib import Path

# Ensure the simulation directory is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from agents import Agent, WorkflowStep
from predictor import Predictor
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
    # 1. Create all 5 agents and initialize simulator
    agents = create_default_agents()
    agent_name_map = {agent.agent_id: f"{agent.agent_type} Agent" for agent in agents}
    sim = MultiAgentSimulator(agents=agents)

    # --- HUMAN READABLE DEMO ---
    print("=== RESERVE-X MULTI-AGENT SIMULATION ===\n")
    print("Active Agents:\n")
    for agent in sim.active_agents:
        print(f"[{agent.agent_id}] {agent.agent_type}")
        print(f"Current: {agent.current_step.name}\n")

    def print_resource_demand(demand: dict[str, dict[str, float]], title: str):
        print(f"=== {title} ===\n")
        # Prioritize key shared resources first
        priority_order = ["LLM", "testing_environment", "terminal", "database", "GPU", "security_scanner", "search_tool", "deployment_environment"]
        sorted_resources = sorted(demand.keys(), key=lambda r: priority_order.index(r) if r in priority_order else 99)
        for res in sorted_resources:
            print(res)
            for agent_id, prob in demand[res].items():
                name = agent_name_map.get(agent_id, agent_id)
                print(f"  {name:<18} {prob:.2f}")
            print()

    demand_tick0 = sim.get_predicted_resource_demand()
    print_resource_demand(demand_tick0, "PREDICTED RESOURCE DEMAND")

    # --- TEST 1: Verify all 5 agents exist, have workflows, and start at correct step ---
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

    # --- TEST 2: Advance simulator by one tick ---
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

    # Show new predictions after tick 1
    demand_tick1 = sim.get_predicted_resource_demand()
    print_resource_demand(demand_tick1, "PREDICTED RESOURCE DEMAND (TICK 1)")

    # --- TEST 3: Verify predictor outputs for all active agents ---
    agent_predictions = sim.get_agent_predictions()
    assert len(agent_predictions) == len(sim.active_agents), "All active agents must produce predictions"
    for agent_id, preds in agent_predictions.items():
        assert len(preds) > 0, f"Agent {agent_id} should have predicted future requirements"
        for resource, prob in preds.items():
            assert 0.0 <= prob <= 1.0, f"Probability for {resource} on {agent_id} must be in [0, 1], got {prob}"

    # --- TEST 4: Verify resource competition & overlapping demands ---
    assert "LLM" in demand_tick0, "LLM should be in resource demand"
    assert "testing_environment" in demand_tick0, "testing_environment should be in resource demand"
    assert len(demand_tick0["LLM"]) >= 3, (
        f"Multiple agents should demand LLM, got {len(demand_tick0['LLM'])}"
    )
    assert len(demand_tick0["testing_environment"]) >= 2, (
        f"Multiple agents should demand testing_environment, got {len(demand_tick0['testing_environment'])}"
    )

    # --- TEST 5: Advance simulation several ticks until agents complete independently ---
    # At tick 1, 4-step agents have 3 steps left.
    # Advancing 3 more ticks (total 4 ticks) completes 4-step agents.
    sim.tick()  # tick 2
    sim.tick()  # tick 3
    sim.tick()  # tick 4

    # Coding agent has 5 steps, so it should still be active on step 'deploy'
    coding_agent = sim.get_agent("agent-001")
    assert not coding_agent.is_complete(), "Coding agent should still be active at tick 4"
    assert coding_agent.current_step.name == "deploy"

    # 4-step agents should be completed
    for aid in ["agent-002", "agent-003", "agent-004", "agent-005"]:
        assert sim.get_agent(aid).is_complete(), f"Agent {aid} should be completed at tick 4"

    # Completed agents must NOT be treated as active future demand
    demand_tick4 = sim.get_predicted_resource_demand()
    for res, agent_probs in demand_tick4.items():
        for aid in agent_probs:
            assert aid == "agent-001", f"Only active agent-001 should be in demand, found {aid}"

    # Advance tick 5 to complete the coding agent as well
    sim.tick()  # tick 5
    assert coding_agent.is_complete(), "Coding agent should be complete at tick 5"
    assert len(sim.active_agents) == 0, "All agents should be completed"
    assert sim.get_predicted_resource_demand() == {}, "Demand must be empty when all agents complete"

    print("PHASE 4 TEST PASSED")


if __name__ == "__main__":
    test_phase_1_basic_agent()
    test_phase_2_workflow_simulation()
    test_phase_3_prediction()
    test_phase_4_multi_agent_simulation()
