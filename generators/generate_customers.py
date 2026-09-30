from pathlib import Path

import pandas as pd
from faker import Faker

from common import (
    load_config,
    initialize_random_seed,
    create_output_directories,
    get_project_root,
    get_regions,
)


def generate_customers():
    # Load configuration
    config = load_config()

    # Initialize reproducible random generation
    initialize_random_seed(config)

    # Create required output folders
    create_output_directories(config)

    # Faker instance
    fake = Faker("en_IN")
    fake.seed_instance(config["project"]["random_seed"])

    # Configuration values
    customer_count = config["record_counts"]["customers"]
    regions = get_regions(config)

    customers = []

    tariffs = [
        "Residential",
        "Commercial",
        "Industrial",
    ]

    segments = [
        "Standard",
        "Premium",
        "High_Usage",
    ]

    for i in range(1, customer_count + 1):
        customer_id = f"CUST{i:05d}"

        customer = {
            "customer_id": customer_id,
            "customer_name": fake.name(),
            "tariff": fake.random_element(tariffs),
            "segment": fake.random_element(segments),
            "region": fake.random_element(regions),
        }

        customers.append(customer)

    # Convert to DataFrame
    df = pd.DataFrame(customers)

    # Output path
    output_dir = (
        get_project_root()
        / config["output"]["customers"]
    )

    output_file = output_dir / "customers.csv"

    # Save CSV
    df.to_csv(output_file, index=False)

    print("Customer dataset generated successfully.")
    print("Rows:", len(df))
    print("Columns:", list(df.columns))
    print("Output:", output_file)


if __name__ == "__main__":
    generate_customers()