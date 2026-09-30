from pathlib import Path
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = PROJECT_ROOT / "config" / "config.yaml"


def load_project_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def copy_file_in_chunks(source_file, destination_file, chunk_size=8 * 1024 * 1024):
    """
    Copy a large file in small chunks so the entire file
    is not loaded into memory.
    """

    total_bytes = source_file.stat().st_size
    copied_bytes = 0

    with open(source_file, "rb") as source:
        with open(destination_file, "wb") as destination:

            while True:
                chunk = source.read(chunk_size)

                if not chunk:
                    break

                destination.write(chunk)
                copied_bytes += len(chunk)

                progress = (copied_bytes / total_bytes) * 100

                print(
                    f"\rProgress: {progress:.1f}%",
                    end=""
                )

    print()


def ingest_meter_readings():
    config = load_project_config()

    raw_path = PROJECT_ROOT / config["data"]["raw_path"]
    bronze_path = PROJECT_ROOT / config["data"]["bronze_path"]

    source_file = raw_path / "meters" / "meter_readings.csv"

    destination_dir = bronze_path / "meters"
    destination_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    destination_file = (
        destination_dir / "meter_readings.csv"
    )

    if not source_file.exists():
        raise FileNotFoundError(
            f"Source file not found: {source_file}"
        )

    print("Starting meter readings Bronze ingestion...")
    print()
    print(f"Source:      {source_file}")
    print(f"Destination: {destination_file}")
    print()

    copy_file_in_chunks(
        source_file,
        destination_file
    )

    source_size = source_file.stat().st_size
    destination_size = destination_file.stat().st_size

    print()
    print(f"Source file size:      {source_size:,} bytes")
    print(f"Bronze file size:      {destination_size:,} bytes")

    if source_size != destination_size:
        raise RuntimeError(
            "File size mismatch. Bronze ingestion may be incomplete."
        )

    print()
    print("Meter readings Bronze ingestion completed successfully.")
    print("Source and Bronze file sizes match.")


if __name__ == "__main__":
    ingest_meter_readings()