# Real-Time Fraud Detection API

A miniature "Stripe Radar": an anomaly-detection model wrapped in a REST API,
with fake transactions streamed through Kafka and scored for risk in real time.

```
Kaggle CSV ──> train.py ──> Isolation Forest (models/iso_forest.joblib)
                                     │
producer.py ──> Kafka topic ──> consumer.py ──> POST /score (FastAPI) ──> risk 0-100
```

## What each piece does

| File | Role |
|------|------|
| `src/train.py` | Trains an Isolation Forest on the Kaggle fraud dataset, evaluates it, saves the model + scaler. |
| `src/model.py` | Loads the model and converts a transaction into a 0-100 risk score. |
| `src/api.py` | FastAPI app exposing `POST /score` and `GET /health`. |
| `src/producer.py` | Replays dataset rows into a Kafka topic to simulate a live stream. |
| `src/consumer.py` | Reads the stream, calls the API for each transaction, prints flagged ones. |
| `docker-compose.yml` | Spins up Kafka + Zookeeper locally. |
| `src/config.py` | All tunable settings (paths, threshold, Kafka broker). |

---

## Step 0 — Prerequisites

- Python 3.10+
- Docker Desktop (for Kafka)
- A Kaggle account

## Step 1 — Set up the project

```bash
cd fraud-detection-api
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Step 2 — Get the data

Download the **Credit Card Fraud Detection** dataset from Kaggle:
https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud

Unzip and place `creditcard.csv` in the `data/` folder:

```
data/creditcard.csv
```

The file has 284,807 transactions with features `V1..V28` (PCA-anonymized),
`Amount`, and `Class` (1 = fraud, 0 = legit). Frauds are ~0.17% of rows — this
class imbalance is exactly why an unsupervised anomaly detector is a good fit.

## Step 3 — Train the model

```bash
python -m src.train
```

This trains an Isolation Forest (unsupervised — it never sees the labels during
fitting), prints a precision/recall report and ROC-AUC against the true labels,
then saves `models/iso_forest.joblib`. Expect ROC-AUC around 0.95.

> Want the autoencoder variant instead? Swap the model in `train.py`: train a
> small Keras autoencoder on the legit rows only, and use reconstruction error
> as the anomaly score. The rest of the pipeline (model.py / api.py) is unchanged
> as long as you keep the same `score_transaction` contract.

## Step 4 — Run the API

```bash
uvicorn src.api:app --reload --port 8000
```

Test it with the interactive docs at http://localhost:8000/docs, or curl:

```bash
curl -X POST http://localhost:8000/score \
  -H "Content-Type: application/json" \
  -d '{"Amount": 999.0, "V1": -3.0, "V14": -8.0}'
```

Response:

```json
{"input_amount": 999.0, "raw_score": 0.18, "risk_score": 73.4, "flagged": true, "threshold": 50.0}
```

## Step 5 — Start Kafka

In a new terminal:

```bash
docker compose up -d
```

This starts Kafka on `localhost:9092`. Check it's healthy with
`docker compose ps`.

## Step 6 — Stream transactions ("real time")

Keep the API running. Open two more terminals (venv activated in each):

**Terminal A — consumer (scores the stream):**
```bash
python -m src.consumer
```

**Terminal B — producer (replays transactions):**
```bash
python -m src.producer --limit 1000 --delay 0.05
```

The producer deliberately mixes known frauds into the stream. Watch the
consumer terminal: it POSTs each transaction to the API and prints the flagged
ones, tagging whether each flag was a true fraud or a false alarm, plus a
running caught/missed tally.

---

## Tuning & next steps

- **Threshold:** raise/lower `RISK_THRESHOLD` (env var or `config.py`) to trade
  off false alarms vs. missed fraud.
- **Contamination:** `CONTAMINATION` tells Isolation Forest how much of the data
  it should treat as anomalous.
- **Persist results:** have the consumer write flagged transactions to Postgres
  or a `flagged.csv` for review.
- **Metrics:** expose Prometheus counters from the API (requests, flag rate,
  latency) and graph them in Grafana.
- **Autoencoder:** compare reconstruction-error scoring against the Isolation
  Forest on the same held-out set.
- **Containerize the API:** add a Dockerfile and put the API in the same compose
  file as Kafka.

## Configuration reference (env vars)

| Var | Default | Meaning |
|-----|---------|---------|
| `DATA_PATH` | `data/creditcard.csv` | Input dataset |
| `MODEL_PATH` | `models/iso_forest.joblib` | Saved model bundle |
| `CONTAMINATION` | `0.0017` | Expected anomaly fraction |
| `RISK_THRESHOLD` | `50` | Flag if risk score >= this |
| `KAFKA_BOOTSTRAP` | `localhost:9092` | Kafka broker |
| `KAFKA_TOPIC` | `transactions` | Topic name |
| `API_URL` | `http://localhost:8000/score` | Endpoint the consumer calls |
