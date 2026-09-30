from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

BRONZE_FILE = (
    PROJECT_ROOT
    / "data"
    / "bronze"
    / "meters"
    / "meters.csv"
)

SILVER_CUSTOMERS_FILE = (
    PROJECT_ROOT
    / "data"
    / "silver"
    / "customers"
    / "customers.csv"
)

SILVER_DIR = (
    PROJECT_ROOT
    / "data"
    / "silver"
    / "meters"
)

SILVER_FILE = SILVER_DIR / "meters.csv"


def transform_meters():

    print("Starting Meters Bronze → Silver transformation...")
    print()

    # --------------------------------------------------
    # 1. Check source files
    # --------------------------------------------------

    if not BRONZE_FILE.exists():
        raise FileNotFoundError(
            f"Bronze meters file not found: {BRONZE_FILE}"
        )

    if not SILVER_CUSTOMERS_FILE.exists():
        raise FileNotFoundError(
            f"Silver customers file not found: "
            f"{SILVER_CUSTOMERS_FILE}"
        )

    # --------------------------------------------------
    # 2. Read Bronze meters
    # --------------------------------------------------

    meters = pd.read_csv(BRONZE_FILE)

    print(f"Bronze meter rows loaded: {len(meters):,}")
    print()

    # --------------------------------------------------
    # 3. Standardize column names
    # --------------------------------------------------

    meters.columns = (
        meters.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )

    # --------------------------------------------------
    # 4. Remove completely empty rows
    # --------------------------------------------------

    meters = meters.dropna(how="all")

    # --------------------------------------------------
    # 5. Validate required columns
    # --------------------------------------------------

    required_columns = [
        "meter_id",
        "customer_id",
        "region",
        "meter_type",
        "installation_date",
        "status"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in meters.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    # --------------------------------------------------
    # 6. Remove duplicate meter records
    # --------------------------------------------------

    rows_before_duplicates = len(meters)

    meters = meters.drop_duplicates(
        subset=["meter_id"]
    )

    duplicates_removed = (
        rows_before_duplicates - len(meters)
    )

    # --------------------------------------------------
    # 7. Standardize text columns
    # --------------------------------------------------

    text_columns = [
        "meter_id",
        "customer_id",
        "region",
        "meter_type",
        "status"
    ]

    for column in text_columns:
        meters[column] = (
            meters[column]
            .astype("string")
            .str.strip()
        )

    # --------------------------------------------------
    # 8. Convert installation date
    # --------------------------------------------------

    meters["installation_date"] = pd.to_datetime(
        meters["installation_date"],
        errors="coerce"
    )

    # --------------------------------------------------
    # 9. Remove records with missing key fields
    # --------------------------------------------------

    meters = meters.dropna(
        subset=[
            "meter_id",
            "customer_id",
            "region"
        ]
    )

    # --------------------------------------------------
    # 10. Validate allowed values
    # --------------------------------------------------

    valid_regions = {
        "North",
        "South",
        "East",
        "West",
        "Central"
    }

    invalid_regions = (
        set(meters["region"].dropna())
        - valid_regions
    )

    if invalid_regions:
        raise ValueError(
            f"Invalid meter regions: {invalid_regions}"
        )

    # --------------------------------------------------
    # 11. Read Silver Customers
    # --------------------------------------------------

    customers = pd.read_csv(
        SILVER_CUSTOMERS_FILE,
        usecols=["customer_id"]
    )

    customers["customer_id"] = (
        customers["customer_id"]
        .astype("string")
        .str.strip()
    )

    # --------------------------------------------------
    # 12. Referential integrity check
    # --------------------------------------------------

    customer_ids = set(
        customers["customer_id"].dropna()
    )

    invalid_customer_ids = set(
        meters["customer_id"].dropna()
    ) - customer_ids

    if invalid_customer_ids:
        raise ValueError(
            f"Found meter records with customer IDs "
            f"not present in Silver Customers. "
            f"Count: {len(invalid_customer_ids)}"
        )

    # --------------------------------------------------
    # 13. Create Silver directory
    # --------------------------------------------------

    SILVER_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------
    # 14. Write Silver meters
    # --------------------------------------------------

    meters.to_csv(
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
        f"{len(meters):,}"
    )

    print(
        f"Invalid customer IDs:     "
        f"{len(invalid_customer_ids)}"
    )

    print(
        f"Null meter IDs:            "
        f"{meters['meter_id'].isna().sum()}"
    )

    print(
        f"Duplicate meter IDs:       "
        f"{meters['meter_id'].duplicated().sum()}"
    )

    print(
        f"Null customer IDs:         "
        f"{meters['customer_id'].isna().sum()}"
    )

    print(
        f"Null regions:              "
        f"{meters['region'].isna().sum()}"
    )

    print(
        f"Null installation dates:   "
        f"{meters['installation_date'].isna().sum()}"
    )

    print()
    print(f"Silver file: {SILVER_FILE}")
    print()
    print("Meters Silver transformation completed successfully.")


if __name__ == "__main__":
    transform_meters()