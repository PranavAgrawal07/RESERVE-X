from __future__ import annotations


class WorkflowStep:
    """
    Represents a single step in an agent's workflow.

    Attributes:
        name: Name of the workflow step (e.g. 'write_code', 'run_tests').
        required_resource: The resource/capability needed for this step.
        duration: Step duration in simulation ticks (default: 1).
    """

    def __init__(self, name: str, required_resource: str, duration: int = 1):
        self.name = name
        self.required_resource = required_resource
        self.duration = duration

    @property
    def resource(self) -> str:
        """Alias for required_resource."""
        return self.required_resource

    def __repr__(self) -> str:
        return (
            f"WorkflowStep(name='{self.name}', "
            f"required_resource='{self.required_resource}', "
            f"duration={self.duration})"
        )

    def __str__(self) -> str:
        return f"{self.name} -> {self.required_resource} (duration: {self.duration} ticks)"


class Agent:
    """
    Agent model for simulating AI agents in RESERVE-X.
    """

    def __init__(
        self,
        agent_id: str,
        agent_type: str,
        current_task: str = "idle",
        workflow_step: str = "init",
        status: str = "idle",
        workflow: list[WorkflowStep] | None = None,
    ):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.current_task = current_task
        self.workflow_step = workflow_step
        self.status = status

        self.workflow: list[WorkflowStep] = []
        self.current_step_index: int = -1

        if workflow is not None:
            self.set_workflow(workflow)

    def set_workflow(self, workflow: list[WorkflowStep | dict]) -> None:
        """
        Assign a workflow to the agent and position it at the first step.
        """
        steps: list[WorkflowStep] = []
        for step in workflow:
            if isinstance(step, WorkflowStep):
                steps.append(step)
            elif isinstance(step, dict):
                steps.append(
                    WorkflowStep(
                        name=step["name"],
                        required_resource=step.get("required_resource") or step.get("resource", "none"),
                        duration=step.get("duration", 1),
                    )
                )
            else:
                steps.append(step)

        self.workflow = steps
        if self.workflow:
            self.current_step_index = 0
            current = self.workflow[0]
            self.current_task = current.name
            self.workflow_step = current.name
            self.status = "busy"
        else:
            self.current_step_index = -1
            self.status = "idle"

    def get_current_step(self) -> WorkflowStep | None:
        """Return the current WorkflowStep or None if completed or unassigned."""
        if 0 <= self.current_step_index < len(self.workflow):
            return self.workflow[self.current_step_index]
        return None

    @property
    def current_step(self) -> WorkflowStep | None:
        """Property alias for get_current_step()."""
        return self.get_current_step()

    def get_upcoming_step(self) -> WorkflowStep | None:
        """Return the upcoming WorkflowStep or None if no next step exists."""
        next_index = self.current_step_index + 1
        if 0 <= next_index < len(self.workflow):
            return self.workflow[next_index]
        return None

    @property
    def upcoming_step(self) -> WorkflowStep | None:
        """Property alias for get_upcoming_step()."""
        return self.get_upcoming_step()

    def is_complete(self) -> bool:
        """Check if all steps in the workflow have been completed."""
        if not self.workflow:
            return False
        return self.current_step_index >= len(self.workflow)

    @property
    def is_completed(self) -> bool:
        """Property alias for is_complete()."""
        return self.is_complete()

    def advance_step(self) -> WorkflowStep | None:
        """
        Advance the agent to the next step in the workflow.
        Returns the new current step, or None if the workflow is completed.
        """
        if not self.workflow or self.current_step_index >= len(self.workflow):
            self.status = "completed"
            return None

        self.current_step_index += 1
        if self.current_step_index < len(self.workflow):
            current = self.workflow[self.current_step_index]
            self.current_task = current.name
            self.workflow_step = current.name
            self.status = "busy"
            return current
        else:
            self.current_task = "completed"
            self.workflow_step = "completed"
            self.status = "completed"
            return None

    def advance(self) -> WorkflowStep | None:
        """Convenience alias for advance_step()."""
        return self.advance_step()

    def update_task(self, task: str, workflow_step: str = None, status: str = None):
        """Update current task, and optionally workflow step and status."""
        self.current_task = task
        if workflow_step is not None:
            self.workflow_step = workflow_step
        if status is not None:
            self.status = status

    def update_workflow_step(self, workflow_step: str):
        """Update workflow step."""
        self.workflow_step = workflow_step

    def update_status(self, status: str):
        """Update agent status."""
        self.status = status

    def __repr__(self):
        return (
            f"Agent(id='{self.agent_id}', "
            f"type='{self.agent_type}', "
            f"task='{self.current_task}', "
            f"step='{self.workflow_step}', "
            f"status='{self.status}')"
        )

    def __str__(self):
        step_display = self.current_step.name if self.current_step else self.workflow_step
        return (
            f"Agent [{self.agent_id}] (Type: {self.agent_type}) | "
            f"Task: {self.current_task} | Step: {step_display} | Status: {self.status}"
        )