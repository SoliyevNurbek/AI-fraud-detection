from __future__ import annotations

import csv
import pickle
from pathlib import Path

from sentrashield_native.ai.model import SimpleFraudModel

ROOT_DIR = Path(__file__).resolve().parents[2]
DATASET_PATH = ROOT_DIR / "data" / "fraud_dataset.csv"
MODEL_PATH = Path(__file__).resolve().with_name("fraud_model.pkl")
FEATURE_NAMES = ["amount", "device_score", "ip_risk", "country_risk", "velocity"]


def _load_dataset() -> tuple[list[list[float]], list[int]]:
    rows: list[list[float]] = []
    labels: list[int] = []
    with DATASET_PATH.open("r", encoding="utf-8", newline="") as dataset:
        reader = csv.DictReader(dataset)
        for record in reader:
            rows.append([float(record[name]) for name in FEATURE_NAMES])
            labels.append(int(record["fraud"]))
    return rows, labels


def _train_fallback_model(rows: list[list[float]], labels: list[int]) -> tuple[object, str]:
    positives = [row for row, label in zip(rows, labels) if label == 1]
    negatives = [row for row, label in zip(rows, labels) if label == 0]
    if not positives or not negatives:
        raise ValueError("Dataset must contain both fraud and non-fraud rows")

    scales = [max(row[index] for row in rows) or 1.0 for index in range(len(FEATURE_NAMES))]
    pos_means = [sum(row[index] for row in positives) / len(positives) for index in range(len(FEATURE_NAMES))]
    neg_means = [sum(row[index] for row in negatives) / len(negatives) for index in range(len(FEATURE_NAMES))]

    weights = []
    for index, scale in enumerate(scales):
        weights.append((pos_means[index] - neg_means[index]) / scale)

    margin = sum(weight * ((pos_means[index] + neg_means[index]) / (2 * scales[index])) for index, weight in enumerate(weights))
    bias = -margin
    model = SimpleFraudModel(weights=weights, bias=bias, feature_names=FEATURE_NAMES)
    return model, model.model_type


def train_model() -> dict[str, str]:
    rows, labels = _load_dataset()

    try:
        import joblib  # type: ignore
        import pandas as pd  # type: ignore
        from xgboost import XGBClassifier  # type: ignore

        dataframe = pd.read_csv(DATASET_PATH)
        X = dataframe[FEATURE_NAMES]
        y = dataframe["fraud"]
        model = XGBClassifier(
            n_estimators=60,
            max_depth=3,
            learning_rate=0.15,
            eval_metric="logloss",
            random_state=42,
        )
        model.fit(X, y)
        artifact = {
            "model": model,
            "feature_names": FEATURE_NAMES,
            "model_version": "xgboost-v1",
        }
        joblib.dump(artifact, MODEL_PATH)
        return {"model_path": str(MODEL_PATH), "model_version": "xgboost-v1"}
    except Exception:
        model, model_version = _train_fallback_model(rows, labels)
        artifact = {
            "model": model,
            "feature_names": FEATURE_NAMES,
            "model_version": model_version,
        }
        with MODEL_PATH.open("wb") as output:
            pickle.dump(artifact, output)
        return {"model_path": str(MODEL_PATH), "model_version": model_version}


if __name__ == "__main__":
    result = train_model()
    print(f"Model trained and saved: {result['model_version']} -> {result['model_path']}")
