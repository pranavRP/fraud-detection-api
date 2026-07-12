"""Load the trained bundle and turn a raw transaction into a 0-100 risk score."""
import joblib
import numpy as np

from . import config

_bundle = None


def load_bundle():
    """Lazy-load the model bundle once per process."""
    global _bundle
    if _bundle is None:
        _bundle = joblib.load(config.MODEL_PATH)
    return _bundle


def score_transaction(tx: dict) -> dict:
    """tx is a dict containing the feature keys (V1..V28, Amount).

    Returns a dict with the raw anomaly score, a normalized 0-100 risk score,
    and a boolean flag.
    """
    bundle = load_bundle()
    model, scaler = bundle["model"], bundle["scaler"]
    features = bundle["features"]

    row = np.array([[tx[f] for f in features]], dtype=float)
    row_scaled = scaler.transform(row)

    # Higher = more anomalous.
    raw = float(-model.decision_function(row_scaled)[0])

    lo, hi = bundle["score_min"], bundle["score_max"]
    risk = 100.0 * (raw - lo) / (hi - lo) if hi > lo else 0.0
    risk = float(np.clip(risk, 0.0, 100.0))

    return {
        "raw_score": raw,
        "risk_score": round(risk, 2),
        "flagged": risk >= config.RISK_THRESHOLD,
        "threshold": config.RISK_THRESHOLD,
    }
