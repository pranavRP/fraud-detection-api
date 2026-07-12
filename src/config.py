"""Central configuration. Override any value via environment variables."""
import os

# --- Paths ---
DATA_PATH = os.getenv("DATA_PATH", "data/creditcard.csv")
MODEL_PATH = os.getenv("MODEL_PATH", "models/iso_forest.joblib")

# --- Feature columns (Kaggle credit-card fraud dataset) ---
# V1..V28 are PCA components; Amount is the transaction amount.
# 'Time' is dropped, 'Class' is the ground-truth label (0=legit, 1=fraud).
FEATURES = [f"V{i}" for i in range(1, 29)] + ["Amount"]
LABEL = "Class"

# --- Model hyperparameters ---
# contamination = expected fraction of anomalies. The real dataset is ~0.0017.
CONTAMINATION = float(os.getenv("CONTAMINATION", "0.0017"))
RANDOM_STATE = 42

# --- Risk scoring ---
# Score threshold (0-100) above which a transaction is flagged.
RISK_THRESHOLD = float(os.getenv("RISK_THRESHOLD", "50"))

# --- Kafka ---
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "transactions")

# --- API ---
API_URL = os.getenv("API_URL", "http://localhost:8000/score")
