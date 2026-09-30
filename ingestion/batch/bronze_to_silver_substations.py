from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

BRONZE_FILE = (
    PROJECT_ROOT
    / "data"
    / "bronze"
    / "substations"
    / "substations.csv"
)

SILVER_DIR = (
    PROJECT_ROOT
    / "data"
    / "silver"
    / "substations"
)

SILVER_FILE = SILVER_DIR / "substations.csv"


def transform_substations():

    print("Starting Substations Bronze → Silver transformation...")
    print()

    # --------------------------------------------------
    # 1. Check source file
    # --------------------------------------------------

    if not BRONZE_FILE.exists():
        raise FileNotFoundError(
            f"Bronze substations file not found: {BRONZE_FILE}"
        )

    # --------------------------------------------------
    # 2. Read Bronze data
    # --------------------------------------------------

    df = pd.read_csv(BRONZE_FILE)

    print(f"Bronze substations rows loaded: {len(df):,}")
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
        "asset_id",
        "region",
        "capacity",
        "status"
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
    # 6. Remove duplicate asset records
    # --------------------------------------------------

    rows_before_duplicates = len(df)

    df = df.drop_duplicates(
        subset=["asset_id"]
    )

    duplicates_removed = (
        rows_before_duplicates - len(df)
    )

    # --------------------------------------------------
    # 7. Standardize text columns
    # --------------------------------------------------

    text_columns = [
        "asset_id",
        "region",
        "status"
    ]

    for column in text_columns:
        df[column] = (
            df[column]
            .astype("string")
            .str.strip()
        )

    # --------------------------------------------------
    # 8. Convert capacity to numeric
    # --------------------------------------------------

    df["capacity"] = pd.to_numeric(
        df["capacity"],
        errors="coerce"
    )

    # --------------------------------------------------
    # 9. Remove records with missing key fields
    # --------------------------------------------------

    df = df.dropna(
        subset=[
            "asset_id",
            "region",
            "capacity",
            "status"
        ]
    )

    # --------------------------------------------------
    # 10. Validate regions
    # --------------------------------------------------

    valid_regions = {
        "North",
        "South",
        "East",
        "West",
        "Central"
    }

    invalid_regions = (
        set(df["region"].dropna())
        - valid_regions
    )

    if invalid_regions:
        raise ValueError(
            f"Invalid region values: {invalid_regions}"
        )

    # --------------------------------------------------
    # 11. Validate capacity
    # --------------------------------------------------

    valid_capacities = {
        50,
        75,
        100,
        150,
        200,
        250
    }

    invalid_capacities = (
        set(df["capacity"].dropna())
        - valid_capacities
    )

    if invalid_capacities:
        raise ValueError(
            f"Invalid capacity values: {invalid_capacities}"
        )

    # --------------------------------------------------
    # 12. Validate status
    # --------------------------------------------------

    valid_statuses = {
        "Operational",
        "Maintenance"
    }

    invalid_statuses = (
        set(df["status"].dropna())
        - valid_statuses
    )

    if invalid_statuses:
        raise ValueError(
            f"Invalid status values: {invalid_statuses}"
        )

    # --------------------------------------------------
    # 13. Create Silver directory
    # --------------------------------------------------

    SILVER_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------
    # 14. Write Silver data
    # --------------------------------------------------

    df.to_csv(
        SILVER_FILE,
        index=False
    )

    # --------------------------------------------------
    # 15. Final validation summary
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
        f"Null asset IDs:            "
        f"{df['asset_id'].isna().sum()}"
    )

    print(
        f"Duplicate asset IDs:       "
        f"{df['asset_id'].duplicated().sum()}"
    )

    print(
        f"Null regions:              "
        f"{df['region'].isna().sum()}"
    )

    print(
        f"Null capacity values:      "
        f"{df['capacity'].isna().sum()}"
    )

    print(
        f"Null status values:        "
        f"{df['status'].isna().sum()}"
    )

    print()
    print(f"Silver file: {SILVER_FILE}")
    print()
    print("Substations Silver transformation completed successfully.")


if __name__ == "__main__":
    transform_substations()