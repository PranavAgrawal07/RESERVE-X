import sys
from pathlib import Path

# Ensure the simulation directory is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from agents import Agent


def test_agent_lifecycle():
    print("--- 1. Creating Agent ---")
    agent = Agent(
        agent_id="agent-001",
        agent_type="coding",
        current_task="writing_code",
        workflow_step="implementation",
        status="busy",
    )

    print("\n--- 2. Initial State ---")
    print(agent)
    assert agent.agent_id == "agent-001"
    assert agent.agent_type == "coding"
    assert agent.current_task == "writing_code"
    assert agent.workflow_step == "implementation"
    assert agent.status == "busy"

    print("\n--- 3. Updating Task and Workflow Step ---")
    agent.update_task("running_unit_tests", workflow_step="testing", status="testing")
    # Demonstrate step and status updates
    agent.update_workflow_step("code_review")
    agent.update_status("reviewing")

    print("\n--- 4. Updated State ---")
    print(agent)

    print("\n--- 5. Verifying Values Changed Correctly ---")
    assert agent.current_task == "running_unit_tests", f"Expected 'running_unit_tests', got {agent.current_task}"
    assert agent.workflow_step == "code_review", f"Expected 'code_review', got {agent.workflow_step}"
    assert agent.status == "reviewing", f"Expected 'reviewing', got {agent.status}"

    print("\nSUCCESS: All agent properties verified successfully!")


if __name__ == "__main__":
    test_agent_lifecycle()
