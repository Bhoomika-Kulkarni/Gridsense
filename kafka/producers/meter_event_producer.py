import csv
import json
import time
from pathlib import Path

from kafka import KafkaProducer


# Project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Silver meter readings file
DATA_FILE = (
    PROJECT_ROOT
    / "data"
    / "silver"
    / "meters"
    / "meter_readings.csv"
)

# Kafka configuration
KAFKA_SERVER = "localhost:9092"
TOPIC_NAME = "grid_meter_events"


def create_producer():
    return KafkaProducer(
        bootstrap_servers=KAFKA_SERVER,
        value_serializer=lambda value: json.dumps(value).encode("utf-8")
    )


def produce_events():
    producer = create_producer()

    print("Starting GridSense Kafka producer...")
    print(f"Reading data from: {DATA_FILE}")
    print(f"Sending events to topic: {TOPIC_NAME}")

    with open(DATA_FILE, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for count, row in enumerate(reader, start=1):

            event = {
                "meter_id": row["meter_id"],
                "customer_id": row["customer_id"],
                "region": row["region"],
                "timestamp": row["timestamp"],
                "kwh": float(row["kwh"]),
                "event_type": "meter_reading"
            }

            producer.send(
                TOPIC_NAME,
                value=event
            )

            producer.flush()

            print(f"Sent event {count}: {event}")

            # Simulate real-time streaming
            time.sleep(1)

            # Stop after 20 events for the first test
            if count >= 20:
                break

    producer.close()

    print("Producer test completed successfully.")


if __name__ == "__main__":
    produce_events()