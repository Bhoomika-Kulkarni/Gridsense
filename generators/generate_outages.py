import pandas as pd
import numpy as np

from common import (
    load_config,
    initialize_random_seed,
    create_output_directories,
    get_project_root,
)


def generate_outages():
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

    outage_count = config["record_counts"]["outages"]

    # Valid outage causes
    causes = [
        "Equipment Failure",
        "Weather",
        "Overload",
        "Vegetation",
        "Animal Interference",
        "Human Error",
        "Scheduled Maintenance",
    ]

    outages = []

    # Date range from configuration
    start_date = pd.Timestamp(
        config["date_range"]["start_date"]
    )

    end_date = pd.Timestamp(
        config["date_range"]["end_date"]
    ) + pd.Timedelta(days=1)

    for i in range(1, outage_count + 1):

        # Select an existing substation
        asset = substations.iloc[
            np.random.randint(0, len(substations))
        ]

        outage_start = start_date + pd.Timedelta(
            seconds=np.random.randint(
                0,
                int((end_date - start_date).total_seconds())
            )
        )

        # Generate outage duration between 15 minutes and 8 hours
        duration_minutes = np.random.randint(15, 481)

        outage_end = outage_start + pd.Timedelta(
            minutes=int(duration_minutes)
        )

        outage = {
            "outage_id": f"OUT{i:05d}",
            "asset_id": asset["asset_id"],
            "start_time": outage_start,
            "end_time": outage_end,
            "cause": np.random.choice(causes),
        }

        outages.append(outage)

    # Convert to DataFrame
    df = pd.DataFrame(outages)

    # Sort chronologically
    df = df.sort_values("start_time").reset_index(drop=True)

    # Output path
    output_dir = (
        get_project_root()
        / config["output"]["outages"]
    )

    output_file = output_dir / "outages.csv"

    # Save CSV
    df.to_csv(output_file, index=False)

    print("Outage dataset generated successfully.")
    print("Rows:", len(df))
    print("Columns:", list(df.columns))
    print("Output:", output_file)


if __name__ == "__main__":
    generate_outages()