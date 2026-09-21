import sys
from pathlib import Path

# Ensure the simulation directory is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from agents import Agent, WorkflowStep


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

    # 1. Create one coding agent
    agent = Agent(agent_id="agent-001", agent_type="coding")

    # 2. Give it the coding workflow
    workflow = [
        WorkflowStep(name="write_code", required_resource="terminal", duration=2),
        WorkflowStep(name="run_tests", required_resource="testing_environment", duration=1),
        WorkflowStep(name="debug", required_resource="LLM", duration=3),
        WorkflowStep(name="run_tests", required_resource="testing_environment", duration=1),
        WorkflowStep(name="deploy", required_resource="deployment_environment", duration=2),
    ]
    agent.set_workflow(workflow)

    # 3. Print the workflow
    print("\nPredefined Coding Workflow:")
    for idx, step in enumerate(workflow, start=1):
        print(f"  Step {idx}: {step.name} -> {step.required_resource} ({step.duration} ticks)")

    # Verify initial state at step 1
    assert not agent.is_complete(), "Workflow should not be complete initially"
    initial_step = agent.get_current_step()
    upcoming_step = agent.get_upcoming_step()
    print(f"\nInitial State: Current Step = '{initial_step.name}' (needs: {initial_step.required_resource}) | Upcoming = '{upcoming_step.name}'")
    assert initial_step.name == "write_code"
    assert upcoming_step.name == "run_tests"

    # 4. Advance the agent one step at a time
    # 5. Print the current step after every transition
    transition = 1
    while not agent.is_complete():
        agent.advance_step()
        current = agent.get_current_step()
        upcoming = agent.get_upcoming_step()
        curr_desc = f"'{current.name}' (needs: {current.required_resource})" if current else "None (Workflow Completed)"
        up_desc = f"'{upcoming.name}'" if upcoming else "None"
        print(f"Transition {transition}: Current Step = {curr_desc} | Upcoming Step = {up_desc}")
        transition += 1

    # 6. Verify that the workflow eventually reaches completion
    assert agent.is_complete() is True, "Workflow should be marked complete"
    assert agent.get_current_step() is None, "Current step should be None after completion"
    assert agent.get_upcoming_step() is None, "Upcoming step should be None after completion"
    assert agent.status == "completed", "Agent status should be 'completed'"

    # 7. Print PHASE 2 TEST PASSED if everything works
    print("\nPHASE 2 TEST PASSED")


if __name__ == "__main__":
    test_phase_1_basic_agent()
    test_phase_2_workflow_simulation()
