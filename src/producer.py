"""Replay the dataset through Kafka to simulate a live transaction stream.

Run (after Kafka is up):
    python -m src.producer            # streams the whole file
    python -m src.producer --limit 500 --delay 0.05
"""
import argparse
import json
import time

import pandas as pd
from kafka import KafkaProducer

from . import config


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=1000,
                        help="max transactions to send (0 = all)")
    parser.add_argument("--delay", type=float, default=0.02,
                        help="seconds to sleep between messages")
    args = parser.parse_args()

    df = pd.read_csv(config.DATA_PATH)
    if args.limit:
        # Mix in known frauds so you can see the API flag them.
        frauds = df[df[config.LABEL] == 1].head(args.limit // 10)
        legit = df[df[config.LABEL] == 0].head(args.limit - len(frauds))
        df = pd.concat([frauds, legit]).sample(frac=1, random_state=1)

    producer = KafkaProducer(
        bootstrap_servers=config.KAFKA_BOOTSTRAP,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )

    print(f"Streaming {len(df)} transactions -> topic '{config.KAFKA_TOPIC}'")
    for i, (_, row) in enumerate(df.iterrows()):
        msg = {f: float(row[f]) for f in config.FEATURES}
        msg["true_label"] = int(row[config.LABEL])  # carried for scoring/metrics
        producer.send(config.KAFKA_TOPIC, msg)
        if i % 100 == 0:
            print(f"  sent {i} ...")
        time.sleep(args.delay)

    producer.flush()
    print("Done.")


if __name__ == "__main__":
    main()
