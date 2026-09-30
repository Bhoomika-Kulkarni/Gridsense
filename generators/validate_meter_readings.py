import pandas as pd

from common import get_project_root, load_config


def validate_meter_readings():
    config = load_config()
    project_root = get_project_root()

    file_path = (
        project_root
        / config["output"]["meters"]
        / "meter_readings.csv"
    )

    required_columns = [
        "meter_id",
        "customer_id",
        "region",
        "timestamp",
        "kwh",
    ]

    total_rows = 0
    unique_meters = set()
    unique_customers = set()
    unique_regions = set()

    duplicate_keys = 0
    missing_values = 0
    negative_kwh = 0

    min_timestamp = None
    max_timestamp = None

    first_chunk = True

    for chunk in pd.read_csv(
        file_path,
        chunksize=100_000,
        parse_dates=["timestamp"]
    ):

        if first_chunk:
            print("Columns:", list(chunk.columns))

            missing_columns = [
                col for col in required_columns
                if col not in chunk.columns
            ]

            if missing_columns:
                raise ValueError(
                    f"Missing columns: {missing_columns}"
                )

            first_chunk = False

        total_rows += len(chunk)

        unique_meters.update(
            chunk["meter_id"].dropna().unique()
        )

        unique_customers.update(
            chunk["customer_id"].dropna().unique()
        )

        unique_regions.update(
            chunk["region"].dropna().unique()
        )

        missing_values += chunk[
            required_columns
        ].isna().sum().sum()

        negative_kwh += (
            chunk["kwh"] < 0
        ).sum()

        duplicate_keys += chunk.duplicated(
            ["meter_id", "timestamp"]
        ).sum()

        chunk_min = chunk["timestamp"].min()
        chunk_max = chunk["timestamp"].max()

        if min_timestamp is None:
            min_timestamp = chunk_min
        else:
            min_timestamp = min(
                min_timestamp,
                chunk_min
            )

        if max_timestamp is None:
            max_timestamp = chunk_max
        else:
            max_timestamp = max(
                max_timestamp,
                chunk_max
            )

    print()
    print("===== METER READINGS VALIDATION =====")
    print("Rows:", total_rows)
    print("Unique meters:", len(unique_meters))
    print("Unique customers:", len(unique_customers))
    print("Regions:", sorted(unique_regions))
    print("Missing values:", missing_values)
    print("Duplicate meter-timestamp records:", duplicate_keys)
    print("Negative kWh values:", negative_kwh)
    print("Minimum timestamp:", min_timestamp)
    print("Maximum timestamp:", max_timestamp)


if __name__ == "__main__":
    validate_meter_readings()