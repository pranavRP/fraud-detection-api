"""Consume the transaction stream, score each message via the API, and print
flagged transactions in real time.

Run (after Kafka + API are up):
    python -m src.consumer
"""
import json

import requests
from kafka import KafkaConsumer

from . import config


def main() -> None:
    consumer = KafkaConsumer(
        config.KAFKA_TOPIC,
        bootstrap_servers=config.KAFKA_BOOTSTRAP,
        auto_offset_reset="latest",
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        group_id="fraud-scorer",
    )

    print(f"Listening on '{config.KAFKA_TOPIC}'. Scoring via {config.API_URL}\n")
    seen = flagged = caught = missed = 0

    for message in consumer:
        tx = message.value
        true_label = tx.pop("true_label", None)

        try:
            resp = requests.post(config.API_URL, json=tx, timeout=5)
            resp.raise_for_status()
            result = resp.json()
        except requests.RequestException as e:
            print(f"[warn] scoring failed: {e}")
            continue

        seen += 1
        if result["flagged"]:
            flagged += 1
            tag = ""
            if true_label is not None:
                tag = " (TRUE FRAUD)" if true_label == 1 else " (false alarm)"
            print(f"FLAGGED risk={result['risk_score']:>6} "
                  f"amount={result['input_amount']:>8.2f}{tag}")

        # Optional live precision/recall if labels are present.
        if true_label is not None:
            if true_label == 1 and result["flagged"]:
                caught += 1
            elif true_label == 1 and not result["flagged"]:
                missed += 1

        if seen % 200 == 0:
            print(f"--- {seen} scored, {flagged} flagged, "
                  f"{caught} frauds caught, {missed} missed ---")


if __name__ == "__main__":
    main()
