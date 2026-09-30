from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

BRONZE_FILE = (
    PROJECT_ROOT
    / "data"
    / "bronze"
    / "customers"
    / "customers.csv"
)

SILVER_DIR = (
    PROJECT_ROOT
    / "data"
    / "silver"
    / "customers"
)

SILVER_FILE = SILVER_DIR / "customers.csv"


def transform_customers():

    print("Starting Customers Bronze → Silver transformation...")
    print()

    # --------------------------------------------------
    # 1. Check source file
    # --------------------------------------------------

    if not BRONZE_FILE.exists():
        raise FileNotFoundError(
            f"Bronze file not found: {BRONZE_FILE}"
        )

    # --------------------------------------------------
    # 2. Read Bronze data
    # --------------------------------------------------

    df = pd.read_csv(BRONZE_FILE)

    print(f"Bronze rows loaded: {len(df):,}")
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
    # 5. Remove duplicate customer records
    # --------------------------------------------------

    before_duplicates = len(df)

    df = df.drop_duplicates(
        subset=["customer_id"]
    )

    duplicates_removed = (
        before_duplicates - len(df)
    )

    # --------------------------------------------------
    # 6. Standardize text fields
    # --------------------------------------------------

    text_columns = [
        "customer_name",
        "tariff",
        "segment",
        "region"
    ]

    for column in text_columns:
        df[column] = (
            df[column]
            .astype("string")
            .str.strip()
        )

    # --------------------------------------------------
    # 7. Validate required fields
    # --------------------------------------------------

    required_columns = [
        "customer_id",
        "customer_name",
        "tariff",
        "segment",
        "region"
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
    # 8. Remove records with missing customer IDs
    # --------------------------------------------------

    df = df.dropna(
        subset=["customer_id"]
    )

    # --------------------------------------------------
    # 9. Validate allowed business values
    # --------------------------------------------------

    valid_tariffs = {
        "Residential",
        "Commercial",
        "Industrial"
    }

    valid_segments = {
        "Standard",
        "Premium",
        "High_Usage"
    }

    valid_regions = {
        "North",
        "South",
        "East",
        "West",
        "Central"
    }

    invalid_tariffs = set(df["tariff"].dropna()) - valid_tariffs
    invalid_segments = set(df["segment"].dropna()) - valid_segments
    invalid_regions = set(df["region"].dropna()) - valid_regions

    if invalid_tariffs:
        raise ValueError(
            f"Invalid tariff values: {invalid_tariffs}"
        )

    if invalid_segments:
        raise ValueError(
            f"Invalid segment values: {invalid_segments}"
        )

    if invalid_regions:
        raise ValueError(
            f"Invalid region values: {invalid_regions}"
        )

    # --------------------------------------------------
    # 10. Create Silver directory
    # --------------------------------------------------

    SILVER_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------
    # 11. Write Silver data
    # --------------------------------------------------

    df.to_csv(
        SILVER_FILE,
        index=False
    )

    # --------------------------------------------------
    # 12. Print validation summary
    # --------------------------------------------------

    print("Transformation completed successfully.")
    print()
    print(f"Original Bronze rows:   {before_duplicates:,}")
    print(f"Duplicates removed:     {duplicates_removed:,}")
    print(f"Final Silver rows:      {len(df):,}")
    print(f"Silver file:            {SILVER_FILE}")
    print()

    print("Silver Customers validation:")
    print(f"Null customer IDs:      {df['customer_id'].isna().sum()}")
    print(f"Duplicate customer IDs: {df['customer_id'].duplicated().sum()}")
    print(f"Null regions:           {df['region'].isna().sum()}")
    print(f"Null tariffs:           {df['tariff'].isna().sum()}")
    print(f"Null segments:          {df['segment'].isna().sum()}")
    print()

    print("Customers Silver transformation completed successfully.")


if __name__ == "__main__":
    transform_customers()