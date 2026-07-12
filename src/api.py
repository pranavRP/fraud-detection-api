"""FastAPI service exposing a real-time /score endpoint.

Run:
    uvicorn src.api:app --reload --port 8000
Then POST a transaction JSON to http://localhost:8000/score
Interactive docs at http://localhost:8000/docs
"""
from fastapi import FastAPI
from pydantic import BaseModel, Field

from . import config
from .model import score_transaction, load_bundle

app = FastAPI(title="Fraud Detection API", version="1.0.0")


class Transaction(BaseModel):
    # V1..V28 PCA components + Amount. Defaults let you test with partial payloads.
    V1: float = 0.0; V2: float = 0.0; V3: float = 0.0; V4: float = 0.0
    V5: float = 0.0; V6: float = 0.0; V7: float = 0.0; V8: float = 0.0
    V9: float = 0.0; V10: float = 0.0; V11: float = 0.0; V12: float = 0.0
    V13: float = 0.0; V14: float = 0.0; V15: float = 0.0; V16: float = 0.0
    V17: float = 0.0; V18: float = 0.0; V19: float = 0.0; V20: float = 0.0
    V21: float = 0.0; V22: float = 0.0; V23: float = 0.0; V24: float = 0.0
    V25: float = 0.0; V26: float = 0.0; V27: float = 0.0; V28: float = 0.0
    Amount: float = Field(0.0, ge=0)


@app.on_event("startup")
def _warm_up():
    # Load the model once at boot so the first request isn't slow.
    load_bundle()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/score")
def score(tx: Transaction):
    result = score_transaction(tx.model_dump())
    return {"input_amount": tx.Amount, **result}
