import pandas as pd
from faker import Faker

from common import (
    load_config,
    initialize_random_seed,
    create_output_directories,
    get_project_root,
    get_regions,
)


def generate_substations():
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
    substation_count = config["record_counts"]["substations"]
    regions = get_regions(config)

    statuses = [
        "Operational",
        "Operational",
        "Operational",
        "Maintenance",
    ]

    substations = []

    for i in range(1, substation_count + 1):
        asset_id = f"AST{i:04d}"

        substation = {
            "asset_id": asset_id,
            "region": fake.random_element(regions),
            "capacity": fake.random_element(
                [
                    50,
                    75,
                    100,
                    150,
                    200,
                    250,
                ]
            ),
            "status": fake.random_element(statuses),
        }

        substations.append(substation)

    # Convert to DataFrame
    df = pd.DataFrame(substations)

    # Output path
    output_dir = (
        get_project_root()
        / config["output"]["substations"]
    )

    output_file = output_dir / "substations.csv"

    # Save CSV
    df.to_csv(output_file, index=False)

    print("Substation dataset generated successfully.")
    print("Rows:", len(df))
    print("Columns:", list(df.columns))
    print("Output:", output_file)


if __name__ == "__main__":
    generate_substations()