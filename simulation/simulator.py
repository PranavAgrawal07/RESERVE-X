from __future__ import annotations

try:
    from .agents import Agent, WorkflowStep
    from .predictor import Predictor
except ImportError:
    from agents import Agent, WorkflowStep
    from predictor import Predictor


def create_default_agents() -> list[Agent]:
    """
    Factory function to instantiate the 5 standard RESERVE-X AI agents
    representing a realistic AI/software company.
    """
    # 1. Coding Agent (5 steps)
    coding_agent = Agent(
        agent_id="agent-001",
        agent_type="Coding",
    )
    coding_agent.set_workflow([
        WorkflowStep(name="write_code", required_resource="terminal", duration=2),
        WorkflowStep(name="run_tests", required_resource="testing_environment", duration=1),
        WorkflowStep(name="debug", required_resource="LLM", duration=3),
        WorkflowStep(name="run_tests", required_resource="testing_environment", duration=1),
        WorkflowStep(name="deploy", required_resource="deployment_environment", duration=2),
    ])
    coding_agent.historical_usage = {
        "LLM": 0.8,
        "testing_environment": 0.9,
        "deployment_environment": 0.4,
    }

    # 2. Research Agent (4 steps)
    research_agent = Agent(
        agent_id="agent-002",
        agent_type="Research",
    )
    research_agent.set_workflow([
        WorkflowStep(name="search_web", required_resource="search_tool", duration=2),
        WorkflowStep(name="analyze_sources", required_resource="LLM", duration=2),
        WorkflowStep(name="summarize", required_resource="LLM", duration=1),
        WorkflowStep(name="generate_report", required_resource="LLM", duration=1),
    ])
    research_agent.historical_usage = {
        "LLM": 0.85,
        "search_tool": 0.8,
    }

    # 3. Testing Agent (4 steps)
    testing_agent = Agent(
        agent_id="agent-003",
        agent_type="Testing",
    )
    testing_agent.set_workflow([
        WorkflowStep(name="prepare_tests", required_resource="testing_environment", duration=1),
        WorkflowStep(name="run_tests", required_resource="testing_environment", duration=2),
        WorkflowStep(name="inspect_failures", required_resource="terminal", duration=1),
        WorkflowStep(name="generate_report", required_resource="LLM", duration=1),
    ])
    testing_agent.historical_usage = {
        "testing_environment": 0.95,
        "terminal": 0.7,
        "LLM": 0.6,
    }

    # 4. Security Agent (4 steps)
    security_agent = Agent(
        agent_id="agent-004",
        agent_type="Security",
    )
    security_agent.set_workflow([
        WorkflowStep(name="scan_code", required_resource="security_scanner", duration=2),
        WorkflowStep(name="analyze_vulnerability", required_resource="LLM", duration=2),
        WorkflowStep(name="run_security_tests", required_resource="testing_environment", duration=2),
        WorkflowStep(name="generate_report", required_resource="LLM", duration=1),
    ])
    security_agent.historical_usage = {
        "security_scanner": 0.85,
        "LLM": 0.75,
        "testing_environment": 0.7,
    }

    # 5. Data Analysis Agent (4 steps)
    data_agent = Agent(
        agent_id="agent-005",
        agent_type="Data Analysis",
    )
    data_agent.set_workflow([
        WorkflowStep(name="load_data", required_resource="database", duration=2),
        WorkflowStep(name="query_database", required_resource="database", duration=2),
        WorkflowStep(name="analyze_data", required_resource="GPU", duration=3),
        WorkflowStep(name="generate_report", required_resource="LLM", duration=1),
    ])
    data_agent.historical_usage = {
        "database": 0.9,
        "GPU": 0.8,
        "LLM": 0.7,
    }

    return [coding_agent, research_agent, testing_agent, security_agent, data_agent]


class MultiAgentSimulator:
    """
    Simulates concurrent execution of multiple AI agents and aggregates their future
    resource dependency predictions for RESERVE-X.
    """

    def __init__(
        self,
        agents: list[Agent] | None = None,
        predictor: Predictor | None = None,
    ):
        self.agents: list[Agent] = []
        self.predictor: Predictor = predictor or Predictor()
        self.current_tick: int = 0

        if agents:
            for agent in agents:
                self.register_agent(agent)

    def register_agent(self, agent: Agent) -> None:
        """Register an agent in the simulation."""
        self.agents.append(agent)

    def add_agent(self, agent: Agent) -> None:
        """Convenience alias for register_agent."""
        self.register_agent(agent)

    def get_agent(self, agent_id: str) -> Agent | None:
        """Retrieve an agent by its ID."""
        for agent in self.agents:
            if agent.agent_id == agent_id:
                return agent
        return None

    @property
    def active_agents(self) -> list[Agent]:
        """Return all agents that have not yet completed their workflows."""
        return [agent for agent in self.agents if not agent.is_complete()]

    def get_active_agents(self) -> list[Agent]:
        """Method alias for active_agents property."""
        return self.active_agents

    def tick(self) -> int:
        """
        Advance all non-completed agents by one simulation tick (one workflow step).
        Returns the updated simulation tick count.
        """
        self.current_tick += 1
        for agent in self.active_agents:
            agent.advance_step()
        return self.current_tick

    def advance_tick(self) -> int:
        """Convenience alias for tick()."""
        return self.tick()

    def get_agent_predictions(self) -> dict[str, dict[str, float]]:
        """
        Run the Predictor on every active agent.
        Returns: {agent_id: {resource: probability, ...}, ...}
        """
        predictions: dict[str, dict[str, float]] = {}
        for agent in self.active_agents:
            preds = self.predictor.predict(agent)
            predictions[agent.agent_id] = preds
        return predictions

    def get_predicted_resource_demand(self) -> dict[str, dict[str, float]]:
        """
        Produce a combined view of predicted resource demand across all active agents.

        Returns:
            dict[str, dict[str, float]]: Mapping of resource -> {agent_id: probability}
            Example:
                {
                    "LLM": {
                        "agent-001": 0.69,
                        "agent-002": 0.85
                    },
                    "testing_environment": {
                        "agent-001": 0.90,
                        "agent-003": 0.95
                    }
                }
        """
        demand: dict[str, dict[str, float]] = {}
        for agent in self.active_agents:
            preds = self.predictor.predict(agent)
            for resource, prob in preds.items():
                if prob > 0.0:
                    if resource not in demand:
                        demand[resource] = {}
                    demand[resource][agent.agent_id] = prob
        return demand
