from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

SILVER_ROOT = PROJECT_ROOT / "data" / "silver"


EXPECTED_COUNTS = {
    "customers": 5_000,
    "meters": 5_000,
    "meter_readings": 8_640_000,
    "substations": 50,
    "outages": 3_000,
    "weather": 10_800,
    "maintenance": 2_000,
}


REQUIRED_COLUMNS = {
    "customers": [
        "customer_id",
        "customer_name",
        "tariff",
        "segment",
        "region",
    ],
    "meters": [
        "meter_id",
        "customer_id",
        "region",
        "meter_type",
        "installation_date",
        "status",
    ],
    "meter_readings": [
        "meter_id",
        "customer_id",
        "region",
        "timestamp",
        "kwh",
    ],
    "substations": [
        "asset_id",
        "region",
        "capacity",
        "status",
    ],
    "outages": [
        "outage_id",
        "asset_id",
        "start_time",
        "end_time",
        "cause",
    ],
    "weather": [
        "location",
        "timestamp",
        "temperature",
        "rainfall",
        "wind",
    ],
    "maintenance": [
        "work_order_id",
        "asset_id",
        "scheduled_date",
        "status",
    ],
}


def check_columns(df, dataset):
    missing = [
        column
        for column in REQUIRED_COLUMNS[dataset]
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            f"{dataset}: missing columns: {missing}"
        )


def check_file(dataset):
    if dataset == "meter_readings":
        file_path = (
            SILVER_ROOT
            / "meters"
            / "meter_readings.csv"
        )
    else:
        file_path = (
            SILVER_ROOT
            / dataset
            / f"{dataset}.csv"
        )

    if not file_path.exists():
        raise FileNotFoundError(
            f"Silver file not found: {file_path}"
        )

    return file_path


def validate_silver():

    print()
    print("=" * 70)
    print("GRIDSENSE SILVER LAYER VALIDATION")
    print("=" * 70)
    print()

    # =========================================================
    # 1. CUSTOMERS
    # =========================================================

    customers_file = check_file("customers")

    customers = pd.read_csv(
        customers_file
    )

    check_columns(
        customers,
        "customers"
    )

    if len(customers) != EXPECTED_COUNTS["customers"]:
        raise ValueError(
            f"Customers expected "
            f"{EXPECTED_COUNTS['customers']:,} rows, "
            f"found {len(customers):,}"
        )

    if customers["customer_id"].isna().any():
        raise ValueError(
            "Customers contain null customer IDs."
        )

    if customers["customer_id"].duplicated().any():
        raise ValueError(
            "Customers contain duplicate customer IDs."
        )

    print(
        f"[OK] customers: "
        f"{len(customers):,} rows"
    )

    # =========================================================
    # 2. METERS
    # =========================================================

    meters_file = check_file("meters")

    meters = pd.read_csv(
        meters_file
    )

    check_columns(
        meters,
        "meters"
    )

    if len(meters) != EXPECTED_COUNTS["meters"]:
        raise ValueError(
            f"Meters expected "
            f"{EXPECTED_COUNTS['meters']:,} rows, "
            f"found {len(meters):,}"
        )

    if meters["meter_id"].isna().any():
        raise ValueError(
            "Meters contain null meter IDs."
        )

    if meters["meter_id"].duplicated().any():
        raise ValueError(
            "Meters contain duplicate meter IDs."
        )

    invalid_meter_customers = (
        set(meters["customer_id"])
        - set(customers["customer_id"])
    )

    if invalid_meter_customers:
        raise ValueError(
            "Meters contain customer IDs "
            "not present in Customers."
        )

    print(
        f"[OK] meters: "
        f"{len(meters):,} rows"
    )

    # =========================================================
    # 3. SUBSTATIONS
    # =========================================================

    substations_file = check_file(
        "substations"
    )

    substations = pd.read_csv(
        substations_file
    )

    check_columns(
        substations,
        "substations"
    )

    if len(substations) != EXPECTED_COUNTS["substations"]:
        raise ValueError(
            f"Substations expected "
            f"{EXPECTED_COUNTS['substations']:,} rows, "
            f"found {len(substations):,}"
        )

    if substations["asset_id"].isna().any():
        raise ValueError(
            "Substations contain null asset IDs."
        )

    if substations["asset_id"].duplicated().any():
        raise ValueError(
            "Substations contain duplicate asset IDs."
        )

    print(
        f"[OK] substations: "
        f"{len(substations):,} rows"
    )

    # =========================================================
    # 4. OUTAGES
    # =========================================================

    outages_file = check_file(
        "outages"
    )

    outages = pd.read_csv(
        outages_file
    )

    check_columns(
        outages,
        "outages"
    )

    if len(outages) != EXPECTED_COUNTS["outages"]:
        raise ValueError(
            f"Outages expected "
            f"{EXPECTED_COUNTS['outages']:,} rows, "
            f"found {len(outages):,}"
        )

    if outages["outage_id"].isna().any():
        raise ValueError(
            "Outages contain null outage IDs."
        )

    if outages["outage_id"].duplicated().any():
        raise ValueError(
            "Outages contain duplicate outage IDs."
        )

    invalid_outage_assets = (
        set(outages["asset_id"])
        - set(substations["asset_id"])
    )

    if invalid_outage_assets:
        raise ValueError(
            "Outages contain invalid asset IDs."
        )

    outages["start_time"] = pd.to_datetime(
        outages["start_time"],
        errors="coerce"
    )

    outages["end_time"] = pd.to_datetime(
        outages["end_time"],
        errors="coerce"
    )

    if outages[
        ["start_time", "end_time"]
    ].isna().any().any():
        raise ValueError(
            "Outages contain invalid timestamps."
        )

    if (
        outages["end_time"]
        < outages["start_time"]
    ).any():
        raise ValueError(
            "Outages contain invalid time ranges."
        )

    print(
        f"[OK] outages: "
        f"{len(outages):,} rows"
    )

    # =========================================================
    # 5. MAINTENANCE
    # =========================================================

    maintenance_file = check_file(
        "maintenance"
    )

    maintenance = pd.read_csv(
        maintenance_file
    )

    check_columns(
        maintenance,
        "maintenance"
    )

    if len(maintenance) != EXPECTED_COUNTS["maintenance"]:
        raise ValueError(
            f"Maintenance expected "
            f"{EXPECTED_COUNTS['maintenance']:,} rows, "
            f"found {len(maintenance):,}"
        )

    if maintenance["work_order_id"].isna().any():
        raise ValueError(
            "Maintenance contains null work order IDs."
        )

    if maintenance["work_order_id"].duplicated().any():
        raise ValueError(
            "Maintenance contains duplicate work order IDs."
        )

    invalid_maintenance_assets = (
        set(maintenance["asset_id"])
        - set(substations["asset_id"])
    )

    if invalid_maintenance_assets:
        raise ValueError(
            "Maintenance contains invalid asset IDs."
        )

    print(
        f"[OK] maintenance: "
        f"{len(maintenance):,} rows"
    )

    # =========================================================
    # 6. WEATHER
    # =========================================================

    weather_file = check_file(
        "weather"
    )

    weather = pd.read_csv(
        weather_file
    )

    check_columns(
        weather,
        "weather"
    )

    if len(weather) != EXPECTED_COUNTS["weather"]:
        raise ValueError(
            f"Weather expected "
            f"{EXPECTED_COUNTS['weather']:,} rows, "
            f"found {len(weather):,}"
        )

    weather["timestamp"] = pd.to_datetime(
        weather["timestamp"],
        errors="coerce"
    )

    if weather["timestamp"].isna().any():
        raise ValueError(
            "Weather contains invalid timestamps."
        )

    if (weather["rainfall"] < 0).any():
        raise ValueError(
            "Weather contains negative rainfall."
        )

    if (weather["wind"] < 0).any():
        raise ValueError(
            "Weather contains negative wind."
        )

    valid_regions = {
        "North",
        "South",
        "East",
        "West",
        "Central",
    }

    invalid_weather_regions = (
        set(weather["location"])
        - valid_regions
    )

    if invalid_weather_regions:
        raise ValueError(
            "Weather contains invalid regions."
        )

    if weather.duplicated(
        subset=["location", "timestamp"]
    ).any():
        raise ValueError(
            "Weather contains duplicate "
            "location + timestamp records."
        )

    print(
        f"[OK] weather: "
        f"{len(weather):,} rows"
    )

    # =========================================================
    # 7. METER READINGS
    # =========================================================

    # IMPORTANT:
    # Meter readings are stored inside the meters folder.

    meter_readings_file = (
        SILVER_ROOT
        / "meters"
        / "meter_readings.csv"
    )

    if not meter_readings_file.exists():
        raise FileNotFoundError(
            f"Silver meter readings file not found: "
            f"{meter_readings_file}"
        )

    # Check columns without loading the full file.

    meter_readings_sample = pd.read_csv(
        meter_readings_file,
        nrows=5
    )

    check_columns(
        meter_readings_sample,
        "meter_readings"
    )

    print(
        "[OK] meter_readings: "
        "required columns verified"
    )

    # ---------------------------------------------------------
    # Meter master lookup
    # ---------------------------------------------------------

    valid_meter_ids = set(
        meters["meter_id"]
    )

    meter_lookup = (
        meters
        .set_index("meter_id")[
            ["customer_id", "region"]
        ]
        .to_dict("index")
    )

    meter_reading_rows = 0
    meter_reading_nulls = 0
    meter_reading_negative = 0
    meter_reading_invalid_meters = 0
    meter_reading_invalid_customers = 0
    meter_reading_invalid_regions = 0
    meter_reading_invalid_timestamps = 0

    print()
    print(
        "Validating meter readings in chunks..."
    )

    for chunk in pd.read_csv(
        meter_readings_file,
        chunksize=100_000
    ):

        meter_reading_rows += len(chunk)

        meter_reading_nulls += (
            chunk[
                [
                    "meter_id",
                    "customer_id",
                    "region",
                    "timestamp",
                    "kwh",
                ]
            ]
            .isna()
            .any(axis=1)
            .sum()
        )

        meter_reading_negative += (
            (chunk["kwh"] < 0)
            .fillna(False)
            .sum()
        )

        meter_reading_invalid_meters += (
            ~chunk["meter_id"].isin(
                valid_meter_ids
            )
        ).sum()

        expected_customers = (
            chunk["meter_id"]
            .map(
                lambda x:
                meter_lookup.get(
                    x,
                    {}
                ).get("customer_id")
            )
        )

        meter_reading_invalid_customers += (
            (
                expected_customers
                != chunk["customer_id"]
            )
            &
            chunk["meter_id"].notna()
            &
            chunk["customer_id"].notna()
        ).sum()

        expected_regions = (
            chunk["meter_id"]
            .map(
                lambda x:
                meter_lookup.get(
                    x,
                    {}
                ).get("region")
            )
        )

        meter_reading_invalid_regions += (
            (
                expected_regions
                != chunk["region"]
            )
            &
            chunk["meter_id"].notna()
            &
            chunk["region"].notna()
        ).sum()

        timestamps = pd.to_datetime(
            chunk["timestamp"],
            errors="coerce"
        )

        meter_reading_invalid_timestamps += (
            timestamps.isna().sum()
        )

    # ---------------------------------------------------------
    # Meter readings final checks
    # ---------------------------------------------------------

    if (
        meter_reading_rows
        != EXPECTED_COUNTS["meter_readings"]
    ):
        raise ValueError(
            f"Meter readings expected "
            f"{EXPECTED_COUNTS['meter_readings']:,} rows, "
            f"found {meter_reading_rows:,}"
        )

    if meter_reading_nulls > 0:
        raise ValueError(
            "Meter readings contain null values."
        )

    if meter_reading_negative > 0:
        raise ValueError(
            "Meter readings contain negative kWh."
        )

    if meter_reading_invalid_meters > 0:
        raise ValueError(
            "Meter readings contain invalid meter IDs."
        )

    if meter_reading_invalid_customers > 0:
        raise ValueError(
            "Meter readings contain invalid customer IDs."
        )

    if meter_reading_invalid_regions > 0:
        raise ValueError(
            "Meter readings contain invalid regions."
        )

    if meter_reading_invalid_timestamps > 0:
        raise ValueError(
            "Meter readings contain invalid timestamps."
        )

    print(
        f"[OK] meter_readings: "
        f"{meter_reading_rows:,} rows"
    )

    # =========================================================
    # FINAL RESULT
    # =========================================================

    print()
    print("=" * 70)
    print("SILVER VALIDATION PASSED")
    print("=" * 70)
    print()

    print(
        "All required Silver datasets exist."
    )

    print(
        "All expected row counts are correct."
    )

    print(
        "Primary-key and referential-integrity checks passed."
    )

    print(
        "Required data-quality checks passed."
    )

    print()
    print(
        "BRONZE → SILVER PIPELINE "
        "COMPLETED SUCCESSFULLY."
    )


if __name__ == "__main__":
    validate_silver()