from datetime import datetime, timedelta
from pathlib import Path
import subprocess

from airflow import DAG
from airflow.operators.python import PythonOperator


PROJECT_ROOT = Path("/opt/gridsense")


default_args = {
    "owner": "gridsense",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
}


def run_command(command):
    result = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True,
        cwd="/opt/gridsense"
    )

    print(result.stdout)

    if result.stderr:
        print(result.stderr)

    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed with exit code {result.returncode}: {command}"
        )

    return result.stdout

def batch_ingestion():
    """
    Copy raw source datasets into the Bronze layer and
    ingest the large meter-reading dataset.
    """
    run_command(
        "python ingestion/batch/ingest_to_bronze.py"
    )

    run_command(
        "python ingestion/batch/ingest_meter_readings_to_bronze.py"
    )


def bronze_validation():
    """Validate that all expected Bronze datasets exist."""
    expected_files = [
        PROJECT_ROOT / "data/bronze/customers/customers.csv",
        PROJECT_ROOT / "data/bronze/meters/meters.csv",
        PROJECT_ROOT / "data/bronze/meters/meter_readings.csv",
        PROJECT_ROOT / "data/bronze/substations/substations.csv",
        PROJECT_ROOT / "data/bronze/outages/outages.csv",
        PROJECT_ROOT / "data/bronze/weather/weather.csv",
        PROJECT_ROOT / "data/bronze/maintenance/maintenance.csv",
    ]

    missing = [str(path) for path in expected_files if not path.exists()]

    if missing:
        raise FileNotFoundError(
            "Bronze validation failed. Missing files:\n"
            + "\n".join(missing)
        )

    print("Bronze validation passed.")
    print(f"Validated {len(expected_files)} Bronze datasets.")


def bronze_to_silver():
    """Transform all Bronze datasets into Silver datasets."""

    scripts = [
        "bronze_to_silver_customers.py",
        "bronze_to_silver_meters.py",
        "bronze_to_silver_meter_readings.py",
        "bronze_to_silver_substations.py",
        "bronze_to_silver_outages.py",
        "bronze_to_silver_weather.py",
        "bronze_to_silver_maintenance.py",
    ]

    for script in scripts:
        run_command(
            f"python ingestion/batch/{script}"
        )


def silver_validation():
    """Run the existing GridSense Silver-layer validation."""
    run_command(
        "python ingestion/batch/validate_silver.py"
    )


def dbt_transformations():
    """Build all dbt models and execute all dbt tests."""
    run_command(
        "cd /opt/gridsense/gridsense_dbt && dbt build"
    )


def demand_forecast():
    """Refresh the demand forecasting model."""
    run_command(
        "python ml/forecasting/train_demand_forecast.py"
    )


def generate_alerts():
    run_command("python -m automation.alerts.generate_alerts")


def send_notifications():
    """Send/audit email and Slack notifications for open alerts."""
    run_command(
        "python automation/notifications/send_alerts.py"
    )


with DAG(
    dag_id="gridsense_pipeline",
    default_args=default_args,
    description="GridSense end-to-end energy data and analytics pipeline",
    schedule="0 2 * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["gridsense", "energy", "analytics"],
) as dag:

    ingestion_task = PythonOperator(
        task_id="batch_ingestion",
        python_callable=batch_ingestion,
    )

    bronze_validation_task = PythonOperator(
        task_id="bronze_validation",
        python_callable=bronze_validation,
    )

    silver_transformation_task = PythonOperator(
        task_id="bronze_to_silver",
        python_callable=bronze_to_silver,
    )

    silver_validation_task = PythonOperator(
        task_id="silver_validation",
        python_callable=silver_validation,
    )

    dbt_task = PythonOperator(
        task_id="dbt_transformations",
        python_callable=dbt_transformations,
    )

    forecast_task = PythonOperator(
        task_id="demand_forecast",
        python_callable=demand_forecast,
    )

    alert_task = PythonOperator(
        task_id="generate_alerts",
        python_callable=generate_alerts,
    )

    notification_task = PythonOperator(
        task_id="send_notifications",
        python_callable=send_notifications,
    )

    (
        ingestion_task
        >> bronze_validation_task
        >> silver_transformation_task
        >> silver_validation_task
        >> dbt_task
        >> forecast_task
        >> alert_task
        >> notification_task
    )