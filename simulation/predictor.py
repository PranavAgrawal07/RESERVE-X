from __future__ import annotations


class Predictor:
    """
    Predictor for estimating future resource/capability needs of AI agents in RESERVE-X.

    Combines:
    1. Workflow evidence: Distance decay based on how close required resources are in
       the remaining workflow, with frequency boost for recurring requirements.
    2. Historical evidence: Frequency with which the agent has historically needed each resource.

    Formula:
        final_probability = workflow_signal * workflow_weight + historical_signal * historical_weight
    """

    def __init__(
        self,
        historical_data: dict[str, float] | None = None,
        workflow_weight: float = 0.7,
        historical_weight: float = 0.3,
    ):
        self.historical_data: dict[str, float] = historical_data or {}
        self.workflow_weight: float = workflow_weight
        self.historical_weight: float = historical_weight

    def predict(
        self, agent, historical_data: dict[str, float] | None = None
    ) -> dict[str, float]:
        """
        Estimate future resource probabilities for the given agent.

        Args:
            agent: The Agent instance to predict resources for.
            historical_data: Optional override for historical resource usage rates.

        Returns:
            dict[str, float]: Mapping of resource name to probability (between 0.0 and 1.0),
                              sorted descending by probability.
        """
        # Edge case 1: Agent has no remaining workflow steps
        if not hasattr(agent, "workflow") or not agent.workflow:
            return {}
        if getattr(agent, "is_complete", lambda: False)():
            return {}
        if agent.current_step_index < 0 or agent.current_step_index >= len(agent.workflow):
            return {}

        # Resolve historical data source
        hist: dict[str, float] = {}
        if historical_data is not None:
            hist = historical_data
        elif hasattr(agent, "historical_usage") and isinstance(agent.historical_usage, dict):
            hist = agent.historical_usage
        elif self.historical_data:
            # Check if self.historical_data is keyed by agent_id or directly by resource
            if hasattr(agent, "agent_id") and agent.agent_id in self.historical_data and isinstance(self.historical_data[agent.agent_id], dict):
                hist = self.historical_data[agent.agent_id]
            else:
                hist = self.historical_data

        # Find remaining steps starting from current position
        remaining_steps = agent.workflow[agent.current_step_index:]
        if not remaining_steps:
            return {}

        # Collect step offsets from current position for each resource
        # offset 0 = current active step (immediate requirement)
        # offset 1 = immediate next step
        # offset 2+ = upcoming steps further down the pipeline
        resource_offsets: dict[str, list[int]] = {}
        for offset, step in enumerate(remaining_steps):
            res = step.required_resource
            if res not in resource_offsets:
                resource_offsets[res] = []
            resource_offsets[res].append(offset)

        predictions: dict[str, float] = {}

        # Compute combined probabilities for resources present in remaining workflow
        for resource, offsets in resource_offsets.items():
            min_offset = min(offsets)

            # 1. Proximity score based on step distance
            if min_offset == 0:
                proximity = 0.95  # Immediate requirement (active step)
            elif min_offset == 1:
                proximity = 0.85  # Very next step
            elif min_offset == 2:
                proximity = 0.65  # Two steps away
            elif min_offset == 3:
                proximity = 0.45  # Three steps away
            else:
                proximity = max(0.15, 0.45 - 0.10 * (min_offset - 3))

            # 2. Recurring frequency boost (if resource appears multiple times in remaining workflow)
            frequency_boost = 0.05 * (len(offsets) - 1)
            workflow_signal = min(1.0, proximity + frequency_boost)

            # 3. Historical behavior signal (treat missing as 0.0)
            historical_signal = float(hist.get(resource, 0.0))
            historical_signal = max(0.0, min(1.0, historical_signal))

            # 4. Combine signals
            final_prob = (
                workflow_signal * self.workflow_weight
                + historical_signal * self.historical_weight
            )

            # 5. Bound probability between 0.0 and 1.0, rounded to 2 decimal places
            bounded_prob = max(0.0, min(1.0, round(final_prob, 2)))
            if bounded_prob > 0.0:
                predictions[resource] = bounded_prob

        # Return sorted by probability descending
        return dict(sorted(predictions.items(), key=lambda item: item[1], reverse=True))
