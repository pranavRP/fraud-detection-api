"""Train an Isolation Forest anomaly detector on the Kaggle credit-card fraud
dataset and persist it (with its feature scaler) to disk.

Usage:
    python -m src.train
Requires data/creditcard.csv (see README for the download link).
"""
import os
import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, roc_auc_score

from . import config


def main() -> None:
    if not os.path.exists(config.DATA_PATH):
        raise FileNotFoundError(
            f"{config.DATA_PATH} not found. Download the Kaggle credit-card "
            "fraud dataset and place creditcard.csv in the data/ folder."
        )

    print(f"Loading {config.DATA_PATH} ...")
    df = pd.read_csv(config.DATA_PATH)

    X = df[config.FEATURES]
    y = df[config.LABEL]  # only used for evaluation, NOT for training

    # Isolation Forest is unsupervised, but scaling Amount keeps it on the same
    # footing as the already-normalized PCA features.
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    print("Training Isolation Forest ...")
    model = IsolationForest(
        n_estimators=200,
        contamination=config.CONTAMINATION,
        random_state=config.RANDOM_STATE,
        n_jobs=-1,
    )
    model.fit(X_scaled)

    # Evaluate against the true labels to sanity-check the detector.
    # decision_function: higher = more normal. Invert so higher = more anomalous.
    anomaly_score = -model.decision_function(X_scaled)
    preds = (model.predict(X_scaled) == -1).astype(int)  # -1 => anomaly => 1

    print("\n=== Evaluation vs. ground truth ===")
    print(classification_report(y, preds, digits=4))
    print(f"ROC-AUC (anomaly score vs. label): {roc_auc_score(y, anomaly_score):.4f}")

    os.makedirs(os.path.dirname(config.MODEL_PATH), exist_ok=True)
    # Persist model + scaler + the score range so the API can normalize to 0-100.
    bundle = {
        "model": model,
        "scaler": scaler,
        "features": config.FEATURES,
        "score_min": float(anomaly_score.min()),
        "score_max": float(anomaly_score.max()),
    }
    joblib.dump(bundle, config.MODEL_PATH)
    print(f"\nSaved model bundle -> {config.MODEL_PATH}")


if __name__ == "__main__":
    main()
