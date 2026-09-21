class Agent:
    """
    Basic Agent model for simulating AI agents in RESERVE-X.
    """

    def __init__(
        self,
        agent_id: str,
        agent_type: str,
        current_task: str = "idle",
        workflow_step: str = "init",
        status: str = "idle",
    ):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.current_task = current_task
        self.workflow_step = workflow_step
        self.status = status

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
        return (
            f"Agent [{self.agent_id}] (Type: {self.agent_type}) | "
            f"Task: {self.current_task} | Step: {self.workflow_step} | Status: {self.status}"
        )