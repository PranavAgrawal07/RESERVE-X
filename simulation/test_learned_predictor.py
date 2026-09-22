"""
Tests for the RESERVE-X Learned Workflow Predictor.

Validates:
1. Model trains successfully on the synthetic historical dataset.
2. Predictions return valid backend capability strings.
3. Probability values are within [0.0, 1.0].
4. Known agent-type/step combinations produce sensible predictions.
5. Unseen inputs produce graceful fallback responses.
6. predict_top_n returns sorted, valid results.
7. The historical dataset itself is well-formed.

Does NOT modify or depend on the existing predictor.py or test_simulation.py.
"""

from __future__ import annotations

import sys
import os

# Ensure the simulation package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from simulation.historical_data import (
    get_training_data,
    HISTORICAL_WORKFLOW_RECORDS,
    VALID_CAPABILITIES,
)
from simulation.learned_predictor import LearnedPredictor


# ────────────────────────────────────────────────────────────────────
# Historical Data Tests
# ────────────────────────────────────────────────────────────────────

class TestHistoricalData:
    """Tests for the historical_data module."""

    def test_dataset_is_non_empty(self):
        data = get_training_data()
        assert len(data) > 0, "Training dataset should not be empty"

    def test_all_records_have_required_keys(self):
        required_keys = {"agent_type", "step_name", "current_capability", "next_capability"}
        for i, record in enumerate(get_training_data()):
            assert required_keys.issubset(record.keys()), (
                f"Record {i} missing keys: {required_keys - record.keys()}"
            )

    def test_all_capabilities_are_valid(self):
        """Every capability in the dataset must be a valid backend CapabilityType."""
        for i, record in enumerate(get_training_data()):
            assert record["current_capability"] in VALID_CAPABILITIES, (
                f"Record {i}: invalid current_capability '{record['current_capability']}'"
            )
            assert record["next_capability"] in VALID_CAPABILITIES, (
                f"Record {i}: invalid next_capability '{record['next_capability']}'"
            )

    def test_dataset_covers_all_agent_types(self):
        """Dataset should cover all 5 standard agent types."""
        agent_types = {r["agent_type"] for r in get_training_data()}
        expected = {"Coding", "Research", "Testing", "Security", "Data Analysis"}
        assert expected.issubset(agent_types), (
            f"Missing agent types: {expected - agent_types}"
        )

    def test_get_training_data_returns_copy(self):
        """get_training_data() should return a copy, not a reference."""
        data1 = get_training_data()
        data2 = get_training_data()
        assert data1 is not data2
        assert data1 == data2

    def test_dataset_has_sufficient_records(self):
        """Need enough records for ML training — at least 20."""
        assert len(get_training_data()) >= 20


# ────────────────────────────────────────────────────────────────────
# LearnedPredictor Training Tests
# ────────────────────────────────────────────────────────────────────

class TestLearnedPredictorTraining:
    """Tests for model training."""

    def test_model_trains_successfully(self):
        predictor = LearnedPredictor(random_state=42)
        assert predictor.is_trained is True

    def test_model_is_deterministic(self):
        """Two predictors with the same seed should produce identical predictions."""
        p1 = LearnedPredictor(random_state=42)
        p2 = LearnedPredictor(random_state=42)

        result1 = p1.predict("Coding", "write_code", "TERMINAL")
        result2 = p2.predict("Coding", "write_code", "TERMINAL")

        assert result1["capability"] == result2["capability"]
        assert result1["probability"] == result2["probability"]

    def test_different_seeds_still_train(self):
        """Model should train with any seed."""
        p = LearnedPredictor(random_state=123)
        assert p.is_trained is True


# ────────────────────────────────────────────────────────────────────
# Prediction Output Format Tests
# ────────────────────────────────────────────────────────────────────

class TestPredictionFormat:
    """Tests for prediction output format and constraints."""

    def setup_method(self):
        self.predictor = LearnedPredictor(random_state=42)

    def test_prediction_returns_dict_with_required_keys(self):
        result = self.predictor.predict("Coding", "write_code", "TERMINAL")
        assert "capability" in result
        assert "probability" in result

    def test_prediction_capability_is_string(self):
        result = self.predictor.predict("Coding", "write_code", "TERMINAL")
        assert isinstance(result["capability"], str)

    def test_prediction_capability_is_valid_backend_type(self):
        result = self.predictor.predict("Coding", "write_code", "TERMINAL")
        assert result["capability"] in VALID_CAPABILITIES, (
            f"Predicted capability '{result['capability']}' not in valid set"
        )

    def test_probability_is_float(self):
        result = self.predictor.predict("Coding", "write_code", "TERMINAL")
        assert isinstance(result["probability"], float)

    def test_probability_in_valid_range(self):
        result = self.predictor.predict("Coding", "write_code", "TERMINAL")
        assert 0.0 <= result["probability"] <= 1.0

    def test_probability_bounded_for_all_agent_types(self):
        """Probability must be in [0, 1] for every agent type."""
        test_cases = [
            ("Coding", "write_code", "TERMINAL"),
            ("Research", "search_web", "WEB_SEARCH"),
            ("Testing", "run_tests", "TESTING"),
            ("Security", "scan_code", "SECURITY_SCAN"),
            ("Data Analysis", "load_data", "DATABASE"),
        ]
        for agent_type, step, cap in test_cases:
            result = self.predictor.predict(agent_type, step, cap)
            assert 0.0 <= result["probability"] <= 1.0, (
                f"Out of range for {agent_type}/{step}/{cap}: {result['probability']}"
            )
            assert result["capability"] in VALID_CAPABILITIES


# ────────────────────────────────────────────────────────────────────
# Known-Pattern Prediction Tests
# ────────────────────────────────────────────────────────────────────

class TestKnownPatterns:
    """Test that the model learns known patterns from the training data."""

    def setup_method(self):
        self.predictor = LearnedPredictor(random_state=42)

    def test_coding_write_code_predicts_testing_or_llm(self):
        """After write_code with TERMINAL, Coding agents typically need TESTING or LLM."""
        result = self.predictor.predict("Coding", "write_code", "TERMINAL")
        # In the dataset, write_code→TERMINAL mostly leads to TESTING
        assert result["capability"] in ("TESTING", "LLM_INFERENCE")
        assert result["probability"] > 0.3  # Should be confident

    def test_research_search_web_predicts_llm(self):
        """Research agents after web search typically need LLM_INFERENCE."""
        result = self.predictor.predict("Research", "search_web", "WEB_SEARCH")
        # Dominant pattern is WEB_SEARCH → LLM_INFERENCE
        assert result["capability"] in ("LLM_INFERENCE", "DATABASE")

    def test_data_analysis_query_database_predicts_gpu(self):
        """Data Analysis agents after database query typically need GPU_COMPUTE."""
        result = self.predictor.predict("Data Analysis", "query_database", "DATABASE")
        assert result["capability"] in ("GPU_COMPUTE", "LLM_INFERENCE")

    def test_security_scan_predicts_llm(self):
        """Security agents after scanning typically need LLM_INFERENCE."""
        result = self.predictor.predict("Security", "scan_code", "SECURITY_SCAN")
        assert result["capability"] in ("LLM_INFERENCE", "SECURITY_SCAN")


# ────────────────────────────────────────────────────────────────────
# Unseen Input / Fallback Tests
# ────────────────────────────────────────────────────────────────────

class TestUnseenInputs:
    """Test graceful handling of inputs not seen during training."""

    def setup_method(self):
        self.predictor = LearnedPredictor(random_state=42)

    def test_unknown_agent_type_returns_fallback(self):
        result = self.predictor.predict("UnknownAgent", "write_code", "TERMINAL")
        assert "capability" in result
        assert "probability" in result
        assert result["capability"] in VALID_CAPABILITIES
        assert 0.0 <= result["probability"] <= 1.0

    def test_unknown_step_name_returns_fallback(self):
        result = self.predictor.predict("Coding", "completely_unknown_step", "TERMINAL")
        assert result["capability"] in VALID_CAPABILITIES
        assert 0.0 <= result["probability"] <= 1.0

    def test_unknown_capability_returns_fallback(self):
        result = self.predictor.predict("Coding", "write_code", "CODE_EXECUTION")
        assert result["capability"] in VALID_CAPABILITIES
        assert 0.0 <= result["probability"] <= 1.0

    def test_all_unknown_returns_fallback(self):
        result = self.predictor.predict("Alien", "warp_drive", "QUANTUM_COMPUTE")
        assert result["capability"] in VALID_CAPABILITIES
        assert result["probability"] == 0.1  # Low confidence fallback


# ────────────────────────────────────────────────────────────────────
# predict_top_n Tests
# ────────────────────────────────────────────────────────────────────

class TestPredictTopN:
    """Tests for the predict_top_n method."""

    def setup_method(self):
        self.predictor = LearnedPredictor(random_state=42)

    def test_top_n_returns_list(self):
        results = self.predictor.predict_top_n("Coding", "write_code", "TERMINAL", n=3)
        assert isinstance(results, list)

    def test_top_n_entries_have_required_keys(self):
        results = self.predictor.predict_top_n("Coding", "write_code", "TERMINAL", n=3)
        for r in results:
            assert "capability" in r
            assert "probability" in r

    def test_top_n_sorted_descending(self):
        results = self.predictor.predict_top_n("Coding", "write_code", "TERMINAL", n=5)
        probs = [r["probability"] for r in results]
        assert probs == sorted(probs, reverse=True), "Results should be sorted descending"

    def test_top_n_all_valid_capabilities(self):
        results = self.predictor.predict_top_n("Research", "search_web", "WEB_SEARCH", n=5)
        for r in results:
            assert r["capability"] in VALID_CAPABILITIES

    def test_top_n_all_probabilities_in_range(self):
        results = self.predictor.predict_top_n("Testing", "run_tests", "TESTING", n=3)
        for r in results:
            assert 0.0 <= r["probability"] <= 1.0

    def test_top_1_matches_predict(self):
        """predict_top_n(n=1) should match predict() output."""
        single = self.predictor.predict("Coding", "write_code", "TERMINAL")
        top1 = self.predictor.predict_top_n("Coding", "write_code", "TERMINAL", n=1)
        assert len(top1) >= 1
        assert top1[0]["capability"] == single["capability"]
        assert top1[0]["probability"] == single["probability"]

    def test_top_n_with_unseen_input(self):
        results = self.predictor.predict_top_n("Alien", "warp", "UNKNOWN", n=3)
        assert len(results) >= 1
        assert results[0]["capability"] in VALID_CAPABILITIES


# ────────────────────────────────────────────────────────────────────
# Independence Tests
# ────────────────────────────────────────────────────────────────────

class TestIndependence:
    """Ensure the learned predictor is independent from the existing predictor."""

    def test_does_not_import_existing_predictor(self):
        """LearnedPredictor module should not reference the Predictor class."""
        import inspect
        from simulation import learned_predictor as lp_module
        source = inspect.getsource(lp_module)
        assert "from .predictor import" not in source
        assert "from predictor import" not in source
        assert "import predictor" not in source

    def test_existing_predictor_still_works(self):
        """Importing LearnedPredictor must not break the existing Predictor."""
        from simulation.predictor import Predictor
        from simulation.agents import Agent, WorkflowStep

        p = Predictor()
        agent = Agent(agent_id="test", agent_type="Coding")
        agent.set_workflow([
            WorkflowStep("step1", "terminal", 1),
            WorkflowStep("step2", "LLM", 1),
        ])
        result = p.predict(agent)
        assert isinstance(result, dict)
        assert len(result) > 0
