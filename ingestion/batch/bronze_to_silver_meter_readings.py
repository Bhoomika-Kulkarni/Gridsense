from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

BRONZE_FILE = (
    PROJECT_ROOT
    / "data"
    / "bronze"
    / "meters"
    / "meter_readings.csv"
)

SILVER_METERS_FILE = (
    PROJECT_ROOT
    / "data"
    / "silver"
    / "meters"
    / "meters.csv"
)

SILVER_DIR = (
    PROJECT_ROOT
    / "data"
    / "silver"
    / "meters"
)

SILVER_FILE = (
    SILVER_DIR
    / "meter_readings.csv"
)

CHUNK_SIZE = 100_000


def transform_meter_readings():

    print("Starting Meter Readings Bronze → Silver transformation...")
    print()

    if not BRONZE_FILE.exists():
        raise FileNotFoundError(
            f"Bronze meter readings file not found: {BRONZE_FILE}"
        )

    if not SILVER_METERS_FILE.exists():
        raise FileNotFoundError(
            f"Silver meters file not found: {SILVER_METERS_FILE}"
        )

    SILVER_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # ---------------------------------------------------------
    # 1. Load valid meter master IDs
    # ---------------------------------------------------------

    meters = pd.read_csv(
        SILVER_METERS_FILE,
        usecols=[
            "meter_id",
            "customer_id",
            "region"
        ]
    )

    meters["meter_id"] = (
        meters["meter_id"]
        .astype("string")
        .str.strip()
    )

    meters["customer_id"] = (
        meters["customer_id"]
        .astype("string")
        .str.strip()
    )

    meters["region"] = (
        meters["region"]
        .astype("string")
        .str.strip()
    )

    valid_meter_ids = set(
        meters["meter_id"].dropna()
    )

    meter_lookup = meters.set_index("meter_id").to_dict(
        "index"
    )

    print(
        f"Valid meter master records: "
        f"{len(valid_meter_ids):,}"
    )

    print()

    # ---------------------------------------------------------
    # 2. Remove existing Silver file
    # ---------------------------------------------------------

    if SILVER_FILE.exists():
        SILVER_FILE.unlink()

    # ---------------------------------------------------------
    # 3. Required columns
    # ---------------------------------------------------------

    required_columns = [
        "meter_id",
        "customer_id",
        "region",
        "timestamp",
        "kwh"
    ]

    # ---------------------------------------------------------
    # 4. Validation counters
    # ---------------------------------------------------------

    total_rows = 0
    valid_rows = 0
    invalid_meter_ids = 0
    invalid_customer_ids = 0
    invalid_regions = 0
    null_values = 0
    negative_kwh = 0
    invalid_timestamps = 0
    duplicate_records = 0

    seen_keys = set()

    first_chunk = True

    # ---------------------------------------------------------
    # 5. Process Bronze file in chunks
    # ---------------------------------------------------------

    reader = pd.read_csv(
        BRONZE_FILE,
        chunksize=CHUNK_SIZE
    )

    for chunk_number, df in enumerate(
        reader,
        start=1
    ):

        print(
            f"Processing chunk {chunk_number}..."
        )

        total_rows += len(df)

        # -----------------------------------------------------
        # Standardize column names
        # -----------------------------------------------------

        df.columns = (
            df.columns
            .str.strip()
            .str.lower()
            .str.replace(" ", "_")
        )

        missing_columns = [
            column
            for column in required_columns
            if column not in df.columns
        ]

        if missing_columns:
            raise ValueError(
                f"Missing required columns: "
                f"{missing_columns}"
            )

        # -----------------------------------------------------
        # Clean text columns
        # -----------------------------------------------------

        text_columns = [
            "meter_id",
            "customer_id",
            "region"
        ]

        for column in text_columns:
            df[column] = (
                df[column]
                .astype("string")
                .str.strip()
            )

        # -----------------------------------------------------
        # Convert timestamp
        # -----------------------------------------------------

        df["timestamp"] = pd.to_datetime(
            df["timestamp"],
            errors="coerce"
        )

        invalid_timestamp_count = (
            df["timestamp"].isna().sum()
        )

        invalid_timestamps += (
            invalid_timestamp_count
        )

        # -----------------------------------------------------
        # Convert kwh
        # -----------------------------------------------------

        df["kwh"] = pd.to_numeric(
            df["kwh"],
            errors="coerce"
        )

        # -----------------------------------------------------
        # Count null values
        # -----------------------------------------------------

        null_count = (
            df[
                [
                    "meter_id",
                    "customer_id",
                    "region",
                    "timestamp",
                    "kwh"
                ]
            ]
            .isna()
            .any(axis=1)
            .sum()
        )

        null_values += null_count

        # -----------------------------------------------------
        # Validate meter IDs
        # -----------------------------------------------------

        meter_valid = (
            df["meter_id"].isin(valid_meter_ids)
        )

        invalid_meter_ids += (
            (~meter_valid).sum()
        )

        # -----------------------------------------------------
        # Validate customer IDs
        # -----------------------------------------------------

        customer_valid = (
            df["meter_id"]
            .map(
                lambda x:
                meter_lookup.get(
                    x,
                    {}
                ).get(
                    "customer_id"
                )
            )
            == df["customer_id"]
        )

        invalid_customer_ids += (
            (
                ~customer_valid
                & df["meter_id"].notna()
                & df["customer_id"].notna()
            ).sum()
        )

        # -----------------------------------------------------
        # Validate regions
        # -----------------------------------------------------

        region_valid = (
            df["meter_id"]
            .map(
                lambda x:
                meter_lookup.get(
                    x,
                    {}
                ).get(
                    "region"
                )
            )
            == df["region"]
        )

        invalid_regions += (
            (
                ~region_valid
                & df["meter_id"].notna()
                & df["region"].notna()
            ).sum()
        )

        # -----------------------------------------------------
        # Validate negative kWh
        # -----------------------------------------------------

        negative_count = (
            (df["kwh"] < 0)
            .fillna(False)
            .sum()
        )

        negative_kwh += negative_count

        # -----------------------------------------------------
        # Duplicate meter + timestamp detection
        # -----------------------------------------------------

        chunk_keys = zip(
            df["meter_id"],
            df["timestamp"]
        )

        for key in chunk_keys:

            if (
                pd.isna(key[0])
                or pd.isna(key[1])
            ):
                continue

            if key in seen_keys:
                duplicate_records += 1
            else:
                seen_keys.add(key)

        # -----------------------------------------------------
        # Build final validity mask
        # -----------------------------------------------------

        valid_mask = (
            df["meter_id"].notna()
            & df["customer_id"].notna()
            & df["region"].notna()
            & df["timestamp"].notna()
            & df["kwh"].notna()
            & meter_valid
            & customer_valid
            & region_valid
            & (df["kwh"] >= 0)
        )

        clean_df = df.loc[
            valid_mask,
            required_columns
        ].copy()

        # -----------------------------------------------------
        # Remove duplicates inside final Silver output
        # -----------------------------------------------------

        clean_df = clean_df.drop_duplicates(
            subset=[
                "meter_id",
                "timestamp"
            ]
        )

        valid_rows += len(clean_df)

        # -----------------------------------------------------
        # Write chunk to Silver
        # -----------------------------------------------------

        clean_df.to_csv(
            SILVER_FILE,
            mode="w" if first_chunk else "a",
            header=first_chunk,
            index=False
        )

        first_chunk = False

    # ---------------------------------------------------------
    # 6. Final validation
    # ---------------------------------------------------------

    print()
    print("=" * 60)
    print("METER READINGS SILVER TRANSFORMATION SUMMARY")
    print("=" * 60)

    print(
        f"Bronze rows processed:     "
        f"{total_rows:,}"
    )

    print(
        f"Final Silver rows:         "
        f"{valid_rows:,}"
    )

    print(
        f"Invalid meter IDs:         "
        f"{invalid_meter_ids:,}"
    )

    print(
        f"Invalid customer IDs:      "
        f"{invalid_customer_ids:,}"
    )

    print(
        f"Invalid regions:           "
        f"{invalid_regions:,}"
    )

    print(
        f"Rows with null values:     "
        f"{null_values:,}"
    )

    print(
        f"Negative kWh records:      "
        f"{negative_kwh:,}"
    )

    print(
        f"Invalid timestamps:        "
        f"{invalid_timestamps:,}"
    )

    print(
        f"Duplicate meter-timestamps:"
        f" {duplicate_records:,}"
    )

    print()
    print(
        f"Silver file: {SILVER_FILE}"
    )

    print()
    print(
        "Meter Readings Silver "
        "transformation completed successfully."
    )


if __name__ == "__main__":
    transform_meter_readings()