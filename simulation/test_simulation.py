import sys
from pathlib import Path

# Ensure the simulation directory is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from agents import Agent, WorkflowStep
from predictor import Predictor


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
    # Setup historical profile
    historical_data = {
        "LLM": 0.8,
        "GPU": 0.4,
        "testing_environment": 0.9,
        "deployment_environment": 0.4,
    }

    predictor = Predictor(historical_data=historical_data)

    # Define standard 5-step workflow
    workflow = [
        WorkflowStep(name="write_code", required_resource="terminal", duration=2),
        WorkflowStep(name="run_tests", required_resource="testing_environment", duration=1),
        WorkflowStep(name="debug", required_resource="LLM", duration=3),
        WorkflowStep(name="run_tests", required_resource="testing_environment", duration=1),
        WorkflowStep(name="deploy", required_resource="deployment_environment", duration=2),
    ]

    agent = Agent(agent_id="agent-001", agent_type="coding")
    agent.set_workflow(workflow)

    # --- HUMAN READABLE DEMO ---
    print("=== RESERVE-X FUTURE DEPENDENCY PREDICTION ===")
    print(f"\nAgent: {agent.agent_id}")
    print(f"Current step: {agent.current_step.name}\n")
    print("Predicted future resource needs:\n")

    preds_step1 = predictor.predict(agent)
    for resource, prob in preds_step1.items():
        print(f"{resource:<24} {prob:.2f}")

    # --- TEST 1: First step prediction verifications ---
    assert "testing_environment" in preds_step1, "testing_environment should be predicted"
    assert "LLM" in preds_step1, "LLM should be predicted"
    assert "deployment_environment" in preds_step1, "deployment_environment should be predicted"
    assert "terminal" in preds_step1, "terminal should be predicted"
    for res, prob in preds_step1.items():
        assert 0.0 <= prob <= 1.0, f"Probability for {res} must be between 0 and 1, got {prob}"

    # Verify GPU from historical is NOT predicted because it is not in remaining workflow (Rule 2)
    assert "GPU" not in preds_step1, "Resources not in workflow must not be predicted"

    # --- TEST 2: Advance to debug step ---
    agent.advance_step()  # step 1: run_tests
    agent.advance_step()  # step 2: debug
    assert agent.current_step.name == "debug"

    print("\n--- Advanced to 'debug' step ---")
    print(f"Agent: {agent.agent_id}")
    print(f"Current step: {agent.current_step.name}\n")
    print("Predicted future resource needs:\n")

    preds_debug = predictor.predict(agent)
    for resource, prob in preds_debug.items():
        print(f"{resource:<24} {prob:.2f}")

    # Verify LLM now has a higher probability because it is the immediate requirement
    assert preds_debug["LLM"] > preds_step1["LLM"], (
        f"LLM probability should increase at 'debug'. Step 1: {preds_step1['LLM']}, Debug: {preds_debug['LLM']}"
    )

    # Verify previously completed resources (terminal) are no longer treated as future requirements
    assert "terminal" not in preds_debug or preds_debug.get("terminal", 0.0) == 0.0, (
        "Completed resource 'terminal' should have 0 probability / be omitted"
    )

    # --- TEST 3: Advance until workflow is complete ---
    while not agent.is_complete():
        agent.advance_step()

    assert agent.is_complete() is True
    preds_complete = predictor.predict(agent)
    assert preds_complete == {}, f"Completed workflow should return empty dict {{}}, got {preds_complete}"

    # --- TEST 4: Historical behavior variation ---
    agent_hist_test = Agent(agent_id="agent-002", agent_type="coding")
    agent_hist_test.set_workflow(workflow)

    hist_a = {"LLM": 0.1}
    hist_b = {"LLM": 0.9}

    pred_a = predictor.predict(agent_hist_test, historical_data=hist_a)
    pred_b = predictor.predict(agent_hist_test, historical_data=hist_b)

    assert pred_b["LLM"] > pred_a["LLM"], (
        f"Expected higher prediction with higher historical usage: {pred_b['LLM']} vs {pred_a['LLM']}"
    )

    print("\nPHASE 3 TEST PASSED")


if __name__ == "__main__":
    test_phase_1_basic_agent()
    test_phase_2_workflow_simulation()
    test_phase_3_prediction()
