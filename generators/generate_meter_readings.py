import pandas as pd
import numpy as np

from common import (
    load_config,
    initialize_random_seed,
    create_output_directories,
    get_project_root,
)


def generate_meter_readings():
    config = load_config()
    initialize_random_seed(config)
    create_output_directories(config)

    project_root = get_project_root()

    # Read meter master data
    meter_file = (
        project_root
        / config["output"]["meters"]
        / "meters.csv"
    )

    meters = pd.read_csv(meter_file)

    # Read customer data to get customer segment
    customer_file = (
        project_root
        / config["output"]["customers"]
        / "customers.csv"
    )

    customers = pd.read_csv(customer_file)

    # Keep only active meters
    active_meters = meters[
        meters["status"].str.lower() == "active"
    ].copy()

    required_meters = config["meter_readings"]["active_meters"]

    if len(active_meters) < required_meters:
        raise ValueError(
            f"Only {len(active_meters)} active meters found. "
            f"Required: {required_meters}"
        )

    # Select required number of meters
    active_meters = active_meters.sample(
        n=required_meters,
        random_state=config["project"]["random_seed"]
    )

    # Add customer segment
    active_meters = active_meters.merge(
        customers[
            ["customer_id", "segment"]
        ],
        on="customer_id",
        how="left"
    )

    # Validate customer mapping
    if active_meters["segment"].isna().any():
        raise ValueError(
            "Some active meters do not have a valid customer segment."
        )

    start_date = pd.Timestamp(
        config["date_range"]["start_date"]
    )

    end_date = pd.Timestamp(
        config["date_range"]["end_date"]
    )

    # Output location
    output_dir = (
        project_root
        / config["output"]["meters"]
    )

    output_file = output_dir / "meter_readings.csv"

    # Remove previous file if it exists
    if output_file.exists():
        output_file.unlink()

    first_chunk = True

    # Generate one day at a time
    current_date = start_date

    while current_date <= end_date:

        timestamps = pd.date_range(
            start=current_date,
            end=current_date + pd.Timedelta(hours=23, minutes=45),
            freq="15min"
        )

        # Repeat every timestamp for all selected meters
        meter_count = len(active_meters)
        timestamp_count = len(timestamps)

        meter_ids = np.tile(
            active_meters["meter_id"].values,
            timestamp_count
        )

        customer_ids = np.tile(
            active_meters["customer_id"].values,
            timestamp_count
        )

        regions = np.tile(
            active_meters["region"].values,
            timestamp_count
        )

        segments = np.tile(
            active_meters["segment"].values,
            timestamp_count
        )

        timestamp_values = np.repeat(
            timestamps.values,
            meter_count
        )

        df = pd.DataFrame({
            "meter_id": meter_ids,
            "customer_id": customer_ids,
            "region": regions,
            "segment": segments,
            "timestamp": timestamp_values,
        })

        # Extract time information
        hours = df["timestamp"].dt.hour
        weekday = df["timestamp"].dt.dayofweek

        # Base consumption by customer segment
        segment_base = df["segment"].map({
            "Standard": 0.30,
            "Premium": 0.50,
            "High_Usage": 0.80,
        }).fillna(0.30)

        # Time-of-day factor
        morning_peak = np.exp(
            -((hours - 8) ** 2) / 8
        )

        evening_peak = np.exp(
            -((hours - 19) ** 2) / 10
        )

        time_factor = (
            0.65
            + 0.35 * morning_peak
            + 0.55 * evening_peak
        )

        # Weekend consumption pattern
        weekend_factor = np.where(
            weekday >= 5,
            1.10,
            1.00
        )

        # Small random variation
        random_factor = np.random.normal(
            loc=1.0,
            scale=0.08,
            size=len(df)
        )

        random_factor = np.clip(
            random_factor,
            0.75,
            1.30
        )

        # Final energy consumption in kWh
        df["kwh"] = (
            segment_base
            * time_factor
            * weekend_factor
            * random_factor
        )

        # Ensure positive values
        df["kwh"] = df["kwh"].clip(
            lower=0.01
        ).round(4)

        # Keep required columns
        df = df[
            [
                "meter_id",
                "customer_id",
                "region",
                "timestamp",
                "kwh",
            ]
        ]

        # Append daily chunk to CSV
        df.to_csv(
            output_file,
            mode="w" if first_chunk else "a",
            header=first_chunk,
            index=False
        )

        first_chunk = False

        print(
            f"Generated readings for "
            f"{current_date.date()}"
        )

        current_date += pd.Timedelta(days=1)

    print()
    print("Meter readings dataset generated successfully.")
    print("Active meters:", required_meters)
    print("Frequency: 15 minutes")
    print("Date range:", start_date.date(), "to", end_date.date())
    print("Output:", output_file)


if __name__ == "__main__":
    generate_meter_readings()