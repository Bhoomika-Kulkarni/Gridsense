from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

BRONZE_PATH = PROJECT_ROOT / "data" / "bronze"


DATASETS = {
    "customers": BRONZE_PATH / "customers" / "customers.csv",
    "meters": BRONZE_PATH / "meters" / "meters.csv",
    "meter_readings": BRONZE_PATH / "meters" / "meter_readings.csv",
    "substations": BRONZE_PATH / "substations" / "substations.csv",
    "outages": BRONZE_PATH / "outages" / "outages.csv",
    "weather": BRONZE_PATH / "weather" / "weather.csv",
    "maintenance": BRONZE_PATH / "maintenance" / "maintenance.csv",
}


def validate_bronze():
    print("=" * 60)
    print("GRIDSENSE BRONZE LAYER VALIDATION")
    print("=" * 60)
    print()

    all_files_exist = True

    for dataset_name, file_path in DATASETS.items():

        if not file_path.exists():
            print(f"[MISSING] {dataset_name}")
            print(f"         {file_path}")
            all_files_exist = False
            continue

        file_size = file_path.stat().st_size

        print(f"[OK] {dataset_name}")
        print(f"     File: {file_path.name}")
        print(f"     Size: {file_size:,} bytes")

        if dataset_name == "meter_readings":
            print("     Note: Large file - row count not loaded into memory.")

        else:
            df = pd.read_csv(file_path)

            print(f"     Rows: {len(df):,}")
            print(f"     Columns: {len(df.columns)}")

        print()

    print("=" * 60)

    if all_files_exist:
        print("BRONZE VALIDATION PASSED")
        print("All required Bronze files are present.")
    else:
        print("BRONZE VALIDATION FAILED")
        print("One or more Bronze files are missing.")

    print("=" * 60)


if __name__ == "__main__":
    validate_bronze()