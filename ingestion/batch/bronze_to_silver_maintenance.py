from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

BRONZE_FILE = (
    PROJECT_ROOT
    / "data"
    / "bronze"
    / "maintenance"
    / "maintenance.csv"
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
    / "maintenance"
)

SILVER_FILE = SILVER_DIR / "maintenance.csv"


def transform_maintenance():

    print("Starting Maintenance Bronze → Silver transformation...")
    print()

    # --------------------------------------------------
    # 1. Check source files
    # --------------------------------------------------

    if not BRONZE_FILE.exists():
        raise FileNotFoundError(
            f"Bronze maintenance file not found: {BRONZE_FILE}"
        )

    if not SILVER_SUBSTATIONS_FILE.exists():
        raise FileNotFoundError(
            f"Silver substations file not found: "
            f"{SILVER_SUBSTATIONS_FILE}"
        )

    # --------------------------------------------------
    # 2. Read Bronze maintenance
    # --------------------------------------------------

    df = pd.read_csv(BRONZE_FILE)

    print(f"Bronze maintenance rows loaded: {len(df):,}")
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
        "work_order_id",
        "asset_id",
        "scheduled_date",
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
    # 6. Remove duplicate work orders
    # --------------------------------------------------

    rows_before_duplicates = len(df)

    df = df.drop_duplicates(
        subset=["work_order_id"]
    )

    duplicates_removed = (
        rows_before_duplicates - len(df)
    )

    # --------------------------------------------------
    # 7. Standardize text columns
    # --------------------------------------------------

    text_columns = [
        "work_order_id",
        "asset_id",
        "status"
    ]

    for column in text_columns:
        df[column] = (
            df[column]
            .astype("string")
            .str.strip()
        )

    # --------------------------------------------------
    # 8. Convert scheduled date
    # --------------------------------------------------

    df["scheduled_date"] = pd.to_datetime(
        df["scheduled_date"],
        errors="coerce"
    )

    # --------------------------------------------------
    # 9. Remove records with missing required values
    # --------------------------------------------------

    df = df.dropna(
        subset=[
            "work_order_id",
            "asset_id",
            "scheduled_date",
            "status"
        ]
    )

    # --------------------------------------------------
    # 10. Validate maintenance statuses
    # --------------------------------------------------

    valid_statuses = {
        "Scheduled",
        "In Progress",
        "Completed",
        "Cancelled"
    }

    invalid_statuses = (
        set(df["status"].dropna())
        - valid_statuses
    )

    if invalid_statuses:
        raise ValueError(
            f"Invalid maintenance statuses: {invalid_statuses}"
        )

    # --------------------------------------------------
    # 11. Read Silver Substations
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
    # 12. Referential integrity check
    # --------------------------------------------------

    valid_asset_ids = set(
        substations["asset_id"].dropna()
    )

    invalid_asset_ids = set(
        df["asset_id"].dropna()
    ) - valid_asset_ids

    if invalid_asset_ids:
        raise ValueError(
            f"Found maintenance records with asset IDs "
            f"not present in Silver Substations. "
            f"Count: {len(invalid_asset_ids)}"
        )

    # --------------------------------------------------
    # 13. Create Silver directory
    # --------------------------------------------------

    SILVER_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------
    # 14. Write Silver maintenance
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
        f"Invalid asset IDs:         "
        f"{len(invalid_asset_ids)}"
    )

    print(
        f"Null work order IDs:       "
        f"{df['work_order_id'].isna().sum()}"
    )

    print(
        f"Duplicate work order IDs:  "
        f"{df['work_order_id'].duplicated().sum()}"
    )

    print(
        f"Null asset IDs:            "
        f"{df['asset_id'].isna().sum()}"
    )

    print(
        f"Null scheduled dates:      "
        f"{df['scheduled_date'].isna().sum()}"
    )

    print(
        f"Null statuses:             "
        f"{df['status'].isna().sum()}"
    )

    print()
    print(f"Silver file: {SILVER_FILE}")
    print()
    print(
        "Maintenance Silver transformation "
        "completed successfully."
    )


if __name__ == "__main__":
    transform_maintenance()