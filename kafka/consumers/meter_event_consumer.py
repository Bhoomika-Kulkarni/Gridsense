import json
from pathlib import Path

from kafka import KafkaConsumer


# Project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Bronze streaming output folder
BRONZE_DIR = PROJECT_ROOT / "data" / "bronze" / "streaming"
BRONZE_DIR.mkdir(parents=True, exist_ok=True)

# Output file
OUTPUT_FILE = BRONZE_DIR / "meter_events.jsonl"

# Kafka configuration
KAFKA_SERVER = "localhost:9092"
TOPIC_NAME = "grid_meter_events"


def create_consumer():
    return KafkaConsumer(
        TOPIC_NAME,
        bootstrap_servers=KAFKA_SERVER,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        group_id="gridsense-meter-consumer",
        value_deserializer=lambda value: json.loads(value.decode("utf-8"))
    )


def consume_events():
    consumer = create_consumer()

    print("Starting GridSense Kafka consumer...")
    print(f"Listening to topic: {TOPIC_NAME}")
    print(f"Writing events to: {OUTPUT_FILE}")

    message_count = 0

    try:
        with open(OUTPUT_FILE, "a", encoding="utf-8") as file:

            for message in consumer:

                event = message.value

                file.write(json.dumps(event) + "\n")
                file.flush()

                message_count += 1

                print(
                    f"Received event {message_count}: "
                    f"{event['meter_id']} | "
                    f"{event['region']} | "
                    f"{event['kwh']} kWh"
                )

                # Stop after 20 events for the first test
                if message_count >= 20:
                    break

    finally:
        consumer.close()

    print(f"Consumer test completed. Events written: {message_count}")


if __name__ == "__main__":
    consume_events()