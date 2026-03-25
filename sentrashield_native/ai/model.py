from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class SimpleFraudModel:
    weights: list[float]
    bias: float
    feature_names: list[str]
    model_type: str = "linear-fallback"

    def predict_proba(self, rows: list[list[float]]) -> list[list[float]]:
        probabilities: list[list[float]] = []
        for row in rows:
            linear = self.bias + sum(weight * value for weight, value in zip(self.weights, row))
            fraud_probability = 1.0 / (1.0 + math.exp(-linear))
            probabilities.append([1.0 - fraud_probability, fraud_probability])
        return probabilities
