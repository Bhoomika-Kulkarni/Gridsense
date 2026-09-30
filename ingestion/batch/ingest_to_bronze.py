from pathlib import Path
import shutil
import sys
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]

CONFIG_PATH = PROJECT_ROOT / "config" / "config.yaml"


def load_project_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def ingest_to_bronze():
    config = load_project_config()

    raw_path = PROJECT_ROOT / config["data"]["raw_path"]
    bronze_path = PROJECT_ROOT / config["data"]["bronze_path"]

    datasets = {
        "customers": "customers/customers.csv",
        "meters": "meters/meters.csv",
        "substations": "substations/substations.csv",
        "outages": "outages/outages.csv",
        "weather": "weather/weather.csv",
        "maintenance": "maintenance/maintenance.csv",
    }

    bronze_path.mkdir(
        parents=True,
        exist_ok=True
    )

    print("Starting Bronze ingestion...")
    print()

    for dataset_name, relative_file in datasets.items():

        source_file = raw_path / relative_file

        if not source_file.exists():
            raise FileNotFoundError(
                f"Source file not found: {source_file}"
            )

        destination_dir = bronze_path / dataset_name

        destination_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        destination_file = (
            destination_dir / Path(relative_file).name
        )

        shutil.copyfile(
            source_file,
            destination_file
        )

        print(
            f"{dataset_name}: "
            f"Bronze ingestion completed"
        )

    print()
    print("Bronze ingestion completed successfully.")


if __name__ == "__main__":
    ingest_to_bronze()