from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

BRONZE_FILE = (
    PROJECT_ROOT
    / "data"
    / "bronze"
    / "weather"
    / "weather.csv"
)

SILVER_DIR = (
    PROJECT_ROOT
    / "data"
    / "silver"
    / "weather"
)

SILVER_FILE = SILVER_DIR / "weather.csv"


def transform_weather():

    print("Starting Weather Bronze → Silver transformation...")
    print()

    if not BRONZE_FILE.exists():
        raise FileNotFoundError(
            f"Bronze weather file not found: {BRONZE_FILE}"
        )

    df = pd.read_csv(BRONZE_FILE)

    print(f"Bronze weather rows loaded: {len(df):,}")
    print()

    # ---------------------------------------------------------
    # 1. Standardize column names
    # ---------------------------------------------------------

    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )

    # ---------------------------------------------------------
    # 2. Remove completely empty rows
    # ---------------------------------------------------------

    df = df.dropna(how="all")

    # ---------------------------------------------------------
    # 3. Validate required columns
    # ---------------------------------------------------------

    required_columns = [
        "location",
        "timestamp",
        "temperature",
        "rainfall",
        "wind"
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

    # ---------------------------------------------------------
    # 4. Remove duplicate location + timestamp records
    # ---------------------------------------------------------

    rows_before_duplicates = len(df)

    df = df.drop_duplicates(
        subset=["location", "timestamp"]
    )

    duplicates_removed = (
        rows_before_duplicates - len(df)
    )

    # ---------------------------------------------------------
    # 5. Clean text columns
    # ---------------------------------------------------------

    df["location"] = (
        df["location"]
        .astype("string")
        .str.strip()
    )

    # ---------------------------------------------------------
    # 6. Convert timestamp
    # ---------------------------------------------------------

    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        errors="coerce"
    )

    # ---------------------------------------------------------
    # 7. Convert numeric columns
    # ---------------------------------------------------------

    numeric_columns = [
        "temperature",
        "rainfall",
        "wind"
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    # ---------------------------------------------------------
    # 8. Remove rows with missing required values
    # ---------------------------------------------------------

    df = df.dropna(
        subset=[
            "location",
            "timestamp",
            "temperature",
            "rainfall",
            "wind"
        ]
    )

    # ---------------------------------------------------------
    # 9. Validate regions
    # ---------------------------------------------------------

    valid_regions = {
        "North",
        "South",
        "East",
        "West",
        "Central"
    }

    invalid_regions = (
        set(df["location"].dropna())
        - valid_regions
    )

    if invalid_regions:
        raise ValueError(
            f"Invalid weather regions found: {invalid_regions}"
        )

    # ---------------------------------------------------------
    # 10. Validate rainfall
    # ---------------------------------------------------------

    invalid_rainfall = (
        df["rainfall"] < 0
    ).sum()

    if invalid_rainfall > 0:
        raise ValueError(
            f"Found {invalid_rainfall} records "
            f"with negative rainfall."
        )

    # ---------------------------------------------------------
    # 11. Validate wind
    # ---------------------------------------------------------

    invalid_wind = (
        df["wind"] < 0
    ).sum()

    if invalid_wind > 0:
        raise ValueError(
            f"Found {invalid_wind} records "
            f"with negative wind values."
        )

    # ---------------------------------------------------------
    # 12. Create Silver directory
    # ---------------------------------------------------------

    SILVER_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # ---------------------------------------------------------
    # 13. Save Silver file
    # ---------------------------------------------------------

    df.to_csv(
        SILVER_FILE,
        index=False
    )

    # ---------------------------------------------------------
    # 14. Validation output
    # ---------------------------------------------------------

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
        f"Invalid regions:           "
        f"{len(invalid_regions)}"
    )

    print(
        f"Negative rainfall records: "
        f"{invalid_rainfall}"
    )

    print(
        f"Negative wind records:     "
        f"{invalid_wind}"
    )

    print(
        f"Null locations:            "
        f"{df['location'].isna().sum()}"
    )

    print(
        f"Null timestamps:           "
        f"{df['timestamp'].isna().sum()}"
    )

    print(
        f"Null temperatures:         "
        f"{df['temperature'].isna().sum()}"
    )

    print(
        f"Null rainfall values:      "
        f"{df['rainfall'].isna().sum()}"
    )

    print(
        f"Null wind values:          "
        f"{df['wind'].isna().sum()}"
    )

    print()

    print(f"Silver file: {SILVER_FILE}")
    print()

    print(
        "Weather Silver transformation "
        "completed successfully."
    )


if __name__ == "__main__":
    transform_weather()