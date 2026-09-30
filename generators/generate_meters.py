from pathlib import Path

import pandas as pd
from faker import Faker

from common import (
    load_config,
    initialize_random_seed,
    create_output_directories,
    get_project_root,
)


def generate_meters():
    # Load configuration
    config = load_config()

    # Initialize reproducible random generation
    initialize_random_seed(config)

    # Create required output folders
    create_output_directories(config)

    # Faker instance
    fake = Faker("en_IN")
    fake.seed_instance(config["project"]["random_seed"])

    # Read the customer dataset
    customer_file = (
        get_project_root()
        / config["output"]["customers"]
        / "customers.csv"
    )

    customers = pd.read_csv(customer_file)

    # Number of meters
    meter_count = config["record_counts"]["meters"]

    # Safety check
    if meter_count > len(customers):
        raise ValueError(
            "Meter count cannot be greater than customer count "
            "because each customer receives one meter."
        )

    # Select customers for meters
    selected_customers = customers.iloc[:meter_count].copy()

    meter_types = [
        "Smart_Meter",
        "Advanced_Smart_Meter",
    ]

    statuses = [
        "Active",
        "Active",
        "Active",
        "Inactive",
    ]

    meters = []

    for i, (_, customer) in enumerate(
        selected_customers.iterrows(),
        start=1,
    ):
        meter_id = f"MTR{i:05d}"

        meter = {
            "meter_id": meter_id,
            "customer_id": customer["customer_id"],
            "region": customer["region"],
            "meter_type": fake.random_element(meter_types),
            "installation_date": fake.date_between(
                start_date="-5y",
                end_date="today",
            ),
            "status": fake.random_element(statuses),
        }

        meters.append(meter)

    # Convert to DataFrame
    df = pd.DataFrame(meters)

    # Output path
    output_dir = (
        get_project_root()
        / config["output"]["meters"]
    )

    output_file = output_dir / "meters.csv"

    # Save CSV
    df.to_csv(output_file, index=False)

    print("Meter master dataset generated successfully.")
    print("Rows:", len(df))
    print("Columns:", list(df.columns))
    print("Output:", output_file)


if __name__ == "__main__":
    generate_meters()