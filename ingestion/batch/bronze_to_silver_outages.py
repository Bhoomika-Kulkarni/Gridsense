from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

BRONZE_FILE = (
    PROJECT_ROOT
    / "data"
    / "bronze"
    / "outages"
    / "outages.csv"
)

SILVER_SUBSTATIONS_FILE = (
    PROJECT_ROOT
    / "data"
    / "silver"
    / "substations"
    / "substations.csv"
)

SILVER_DIR = (
    PROJECT_ROOT
    / "data"
    / "silver"
    / "outages"
)

SILVER_FILE = SILVER_DIR / "outages.csv"


def transform_outages():

    print("Starting Outages Bronze → Silver transformation...")
    print()

    # --------------------------------------------------
    # 1. Check source files
    # --------------------------------------------------

    if not BRONZE_FILE.exists():
        raise FileNotFoundError(
            f"Bronze outages file not found: {BRONZE_FILE}"
        )

    if not SILVER_SUBSTATIONS_FILE.exists():
        raise FileNotFoundError(
            f"Silver substations file not found: "
            f"{SILVER_SUBSTATIONS_FILE}"
        )

    # --------------------------------------------------
    # 2. Read Bronze outages
    # --------------------------------------------------

    df = pd.read_csv(BRONZE_FILE)

    print(f"Bronze outage rows loaded: {len(df):,}")
    print()

    # --------------------------------------------------
    # 3. Standardize column names
    # --------------------------------------------------

    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )

    # --------------------------------------------------
    # 4. Remove completely empty rows
    # --------------------------------------------------

    df = df.dropna(how="all")

    # --------------------------------------------------
    # 5. Validate required columns
    # --------------------------------------------------

    required_columns = [
        "outage_id",
        "asset_id",
        "start_time",
        "end_time",
        "cause"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    # --------------------------------------------------
    # 6. Remove duplicate outage records
    # --------------------------------------------------

    rows_before_duplicates = len(df)

    df = df.drop_duplicates(
        subset=["outage_id"]
    )

    duplicates_removed = (
        rows_before_duplicates - len(df)
    )

    # --------------------------------------------------
    # 7. Standardize text columns
    # --------------------------------------------------

    text_columns = [
        "outage_id",
        "asset_id",
        "cause"
    ]

    for column in text_columns:
        df[column] = (
            df[column]
            .astype("string")
            .str.strip()
        )

    # --------------------------------------------------
    # 8. Convert timestamps
    # --------------------------------------------------

    df["start_time"] = pd.to_datetime(
        df["start_time"],
        errors="coerce"
    )

    df["end_time"] = pd.to_datetime(
        df["end_time"],
        errors="coerce"
    )

    # --------------------------------------------------
    # 9. Remove records with missing required values
    # --------------------------------------------------

    df = df.dropna(
        subset=[
            "outage_id",
            "asset_id",
            "start_time",
            "end_time",
            "cause"
        ]
    )

    # --------------------------------------------------
    # 10. Validate outage time range
    # --------------------------------------------------

    invalid_time_ranges = (
        df["end_time"] < df["start_time"]
    )

    invalid_time_count = invalid_time_ranges.sum()

    if invalid_time_count > 0:
        raise ValueError(
            f"Found {invalid_time_count} outages "
            f"where end_time is earlier than start_time."
        )

    # --------------------------------------------------
    # 11. Validate outage causes
    # --------------------------------------------------

    valid_causes = {
        "Equipment Failure",
        "Weather",
        "Overload",
        "Vegetation",
        "Animal Interference",
        "Human Error",
        "Scheduled Maintenance"
    }

    invalid_causes = (
        set(df["cause"].dropna())
        - valid_causes
    )

    if invalid_causes:
        raise ValueError(
            f"Invalid outage causes: {invalid_causes}"
        )

    # --------------------------------------------------
    # 12. Read Silver Substations
    # --------------------------------------------------

    substations = pd.read_csv(
        SILVER_SUBSTATIONS_FILE,
        usecols=["asset_id"]
    )

    substations["asset_id"] = (
        substations["asset_id"]
        .astype("string")
        .str.strip()
    )

    # --------------------------------------------------
    # 13. Referential integrity check
    # --------------------------------------------------

    valid_asset_ids = set(
        substations["asset_id"].dropna()
    )

    invalid_asset_ids = set(
        df["asset_id"].dropna()
    ) - valid_asset_ids

    if invalid_asset_ids:
        raise ValueError(
            f"Found outage records with asset IDs "
            f"not present in Silver Substations. "
            f"Count: {len(invalid_asset_ids)}"
        )

    # --------------------------------------------------
    # 14. Create Silver directory
    # --------------------------------------------------

    SILVER_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------
    # 15. Write Silver outages
    # --------------------------------------------------

    df.to_csv(
        SILVER_FILE,
        index=False
    )

    # --------------------------------------------------
    # 16. Final validation summary
    # --------------------------------------------------

    print("Transformation completed successfully.")
    print()

    print(
        f"Original Bronze rows:     "
        f"{rows_before_duplicates:,}"
    )

    print(
        f"Duplicates removed:       "
        f"{duplicates_removed:,}"
    )

    print(
        f"Final Silver rows:        "
        f"{len(df):,}"
    )

    print(
        f"Invalid asset IDs:         "
        f"{len(invalid_asset_ids)}"
    )

    print(
        f"Invalid time ranges:       "
        f"{invalid_time_count}"
    )

    print(
        f"Null outage IDs:           "
        f"{df['outage_id'].isna().sum()}"
    )

    print(
        f"Duplicate outage IDs:      "
        f"{df['outage_id'].duplicated().sum()}"
    )

    print(
        f"Null asset IDs:            "
        f"{df['asset_id'].isna().sum()}"
    )

    print(
        f"Null causes:               "
        f"{df['cause'].isna().sum()}"
    )

    print()
    print(f"Silver file: {SILVER_FILE}")
    print()
    print("Outages Silver transformation completed successfully.")


if __name__ == "__main__":
    transform_outages()