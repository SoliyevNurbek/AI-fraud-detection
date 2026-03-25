from __future__ import annotations

import pickle
from functools import lru_cache
from pathlib import Path

from sentrashield_native.ai.train_model import FEATURE_NAMES, train_model

MODEL_PATH = Path(__file__).resolve().with_name("fraud_model.pkl")


def _load_joblib_artifact():
    import joblib  # type: ignore

    return joblib.load(MODEL_PATH)


@lru_cache(maxsize=1)
def load_model_artifact() -> dict[str, object]:
    if not MODEL_PATH.exists():
        train_model()

    try:
        return _load_joblib_artifact()
    except Exception:
        with MODEL_PATH.open("rb") as model_file:
            return pickle.load(model_file)


def predict_risk(features: dict[str, float]) -> tuple[float, str, str]:
    artifact = load_model_artifact()
    model = artifact["model"]
    feature_names = artifact.get("feature_names", FEATURE_NAMES)
    row = [[float(features[name]) for name in feature_names]]
    probability = model.predict_proba(row)[0][1]
    score = round(probability * 100, 2)

    if score > 80:
        decision = "block"
    elif score > 60:
        decision = "review"
    elif score > 30:
        decision = "monitor"
    else:
        decision = "allow"

    return score, decision, str(artifact.get("model_version", "unknown"))
