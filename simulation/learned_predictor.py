"""
Learned Workflow Predictor for RESERVE-X.

An independent, ML-based predictor that uses historical workflow execution
data to predict the next capability an agent will need. Uses scikit-learn's
RandomForestClassifier trained on the synthetic dataset from historical_data.py.

This module does NOT modify or replace the existing Predictor in predictor.py.
It is a standalone module that future autonomous simulation can call.

Returns predictions using backend CapabilityType strings directly:
    GPU_COMPUTE, CODE_EXECUTION, WEB_SEARCH, LLM_INFERENCE,
    TESTING, TERMINAL, DATABASE, SECURITY_SCAN, DEPLOYMENT
"""

from __future__ import annotations

from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

try:
    from .historical_data import get_training_data, VALID_CAPABILITIES
except ImportError:
    from historical_data import get_training_data, VALID_CAPABILITIES


class LearnedPredictor:
    """
    ML-based predictor for next-capability prediction.

    Trains a RandomForestClassifier on historical workflow execution data.
    Given the current agent type, step name, and current capability,
    predicts the next capability the agent will need.

    This is independent of the existing heuristic Predictor and can be
    used alongside it by future autonomous simulation features.
    """

    def __init__(self, random_state: int = 42):
        """
        Initialize and train the predictor.

        Args:
            random_state: Seed for reproducibility in both the classifier
                          and any internal randomness.
        """
        self.random_state = random_state

        # Label encoders for categorical features
        self._agent_type_encoder = LabelEncoder()
        self._step_name_encoder = LabelEncoder()
        self._current_cap_encoder = LabelEncoder()
        self._target_encoder = LabelEncoder()

        # The trained model
        self._model: RandomForestClassifier | None = None
        self._is_trained: bool = False

        # Train immediately on construction
        self._train()

    def _train(self) -> None:
        """Train the model on the historical dataset."""
        data = get_training_data()

        if not data:
            raise ValueError("Historical dataset is empty; cannot train.")

        # Extract features and labels
        agent_types = [r["agent_type"] for r in data]
        step_names = [r["step_name"] for r in data]
        current_caps = [r["current_capability"] for r in data]
        next_caps = [r["next_capability"] for r in data]

        # Fit encoders
        self._agent_type_encoder.fit(agent_types)
        self._step_name_encoder.fit(step_names)
        self._current_cap_encoder.fit(current_caps)
        self._target_encoder.fit(next_caps)

        # Encode features → numeric matrix
        X = list(zip(
            self._agent_type_encoder.transform(agent_types),
            self._step_name_encoder.transform(step_names),
            self._current_cap_encoder.transform(current_caps),
        ))

        # Encode target
        y = self._target_encoder.transform(next_caps)

        # Train
        self._model = RandomForestClassifier(
            n_estimators=50,
            max_depth=8,
            random_state=self.random_state,
        )
        self._model.fit(X, y)
        self._is_trained = True

    @property
    def is_trained(self) -> bool:
        """Whether the model has been successfully trained."""
        return self._is_trained

    def predict(
        self,
        agent_type: str,
        step_name: str,
        current_capability: str,
    ) -> dict[str, str | float]:
        """
        Predict the next required capability.

        Args:
            agent_type: The type of agent (e.g. 'Coding', 'Research').
            step_name: The current workflow step name (e.g. 'write_code').
            current_capability: The backend capability currently in use
                                (e.g. 'TERMINAL').

        Returns:
            dict with keys:
                - "capability": str — predicted next backend capability
                - "probability": float — confidence ∈ [0.0, 1.0]

        Raises:
            RuntimeError: If the model has not been trained.
            ValueError: If an unseen categorical value is provided that the
                        encoder cannot handle.
        """
        if not self._is_trained or self._model is None:
            raise RuntimeError("Model is not trained. Cannot predict.")

        # Encode input — handle unseen labels gracefully
        try:
            at_enc = self._agent_type_encoder.transform([agent_type])[0]
        except ValueError:
            # Unknown agent type: fall back to most common prediction
            return self._fallback_prediction()

        try:
            sn_enc = self._step_name_encoder.transform([step_name])[0]
        except ValueError:
            return self._fallback_prediction()

        try:
            cc_enc = self._current_cap_encoder.transform([current_capability])[0]
        except ValueError:
            return self._fallback_prediction()

        sample = [[at_enc, sn_enc, cc_enc]]

        # predict_proba gives class probabilities
        probas = self._model.predict_proba(sample)[0]
        best_idx = probas.argmax()
        best_prob = float(probas[best_idx])
        best_cap = self._target_encoder.inverse_transform([best_idx])[0]

        return {
            "capability": str(best_cap),
            "probability": round(best_prob, 4),
        }

    def predict_top_n(
        self,
        agent_type: str,
        step_name: str,
        current_capability: str,
        n: int = 3,
    ) -> list[dict[str, str | float]]:
        """
        Return top-N predictions sorted by probability (descending).

        Args:
            agent_type: Agent type string.
            step_name: Current step name.
            current_capability: Current backend capability.
            n: Number of top predictions to return.

        Returns:
            List of dicts, each with "capability" and "probability" keys.
        """
        if not self._is_trained or self._model is None:
            raise RuntimeError("Model is not trained. Cannot predict.")

        try:
            at_enc = self._agent_type_encoder.transform([agent_type])[0]
            sn_enc = self._step_name_encoder.transform([step_name])[0]
            cc_enc = self._current_cap_encoder.transform([current_capability])[0]
        except ValueError:
            # Unseen label — return single fallback
            return [self._fallback_prediction()]

        sample = [[at_enc, sn_enc, cc_enc]]
        probas = self._model.predict_proba(sample)[0]

        # Sort indices by probability descending
        sorted_indices = probas.argsort()[::-1][:n]

        results = []
        for idx in sorted_indices:
            prob = float(probas[idx])
            if prob > 0.0:
                cap = self._target_encoder.inverse_transform([idx])[0]
                results.append({
                    "capability": str(cap),
                    "probability": round(prob, 4),
                })

        return results

    def _fallback_prediction(self) -> dict[str, str | float]:
        """
        Return a low-confidence fallback prediction for unseen inputs.
        Uses the most common class in training data.
        """
        data = get_training_data()
        from collections import Counter
        counts = Counter(r["next_capability"] for r in data)
        most_common_cap = counts.most_common(1)[0][0]
        return {
            "capability": most_common_cap,
            "probability": 0.1,  # Low confidence for unseen inputs
        }
