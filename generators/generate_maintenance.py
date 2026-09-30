import pandas as pd
import numpy as np

from common import (
    load_config,
    initialize_random_seed,
    create_output_directories,
    get_project_root,
)


def generate_maintenance():
    # Load configuration
    config = load_config()

    # Initialize reproducible random generation
    initialize_random_seed(config)

    # Create required output folders
    create_output_directories(config)

    # Read the substation dataset
    substation_file = (
        get_project_root()
        / config["output"]["substations"]
        / "substations.csv"
    )

    substations = pd.read_csv(substation_file)

    maintenance_count = config["record_counts"]["maintenance"]

    statuses = [
        "Scheduled",
        "In Progress",
        "Completed",
        "Completed",
        "Cancelled",
    ]

    maintenance = []

    # Date range from configuration
    start_date = pd.Timestamp(
        config["date_range"]["start_date"]
    )

    end_date = pd.Timestamp(
        config["date_range"]["end_date"]
    )

    for i in range(1, maintenance_count + 1):

        # Select an existing asset
        asset = substations.iloc[
            np.random.randint(0, len(substations))
        ]

        scheduled_date = start_date + pd.Timedelta(
            days=np.random.randint(
                0,
                (end_date - start_date).days + 1
            )
        )

        record = {
            "work_order_id": f"WO{i:05d}",
            "asset_id": asset["asset_id"],
            "scheduled_date": scheduled_date.date(),
            "status": np.random.choice(statuses),
        }

        maintenance.append(record)

    # Convert to DataFrame
    df = pd.DataFrame(maintenance)

    # Sort by scheduled date
    df = df.sort_values(
        "scheduled_date"
    ).reset_index(drop=True)

    # Output path
    output_dir = (
        get_project_root()
        / config["output"]["maintenance"]
    )

    output_file = output_dir / "maintenance.csv"

    # Save CSV
    df.to_csv(output_file, index=False)

    print("Maintenance dataset generated successfully.")
    print("Rows:", len(df))
    print("Columns:", list(df.columns))
    print("Output:", output_file)


if __name__ == "__main__":
    generate_maintenance()