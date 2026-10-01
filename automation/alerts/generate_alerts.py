import os
from collections import defaultdict

import psycopg2

from automation.rules.alert_rules import (
    PEAK_DEMAND_ALERT,
    calculate_threshold,
    build_peak_demand_alert,
)


def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.getenv("DB_NAME", "gridsense"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD"),
    )


def load_forecasts(connection):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                forecast_date,
                region_name,
                predicted_kwh
            FROM warehouse.fact_demand_forecast
            ORDER BY region_name, forecast_date;
        """)
        return cursor.fetchall()


def generate_peak_demand_alerts():
    connection = get_connection()

    try:
        forecasts = load_forecasts(connection)

        if not forecasts:
            raise ValueError(
                "Alert generation failed: warehouse.fact_demand_forecast is empty."
            )

        regional_values = defaultdict(list)
        for forecast_date, region_name, predicted_kwh in forecasts:
            regional_values[region_name].append(float(predicted_kwh))

        regional_thresholds = {
            region: calculate_threshold(values)
            for region, values in regional_values.items()
        }

        inserted = 0
        skipped = 0

        with connection.cursor() as cursor:
            for forecast_date, region_name, predicted_kwh in forecasts:
                predicted_kwh = float(predicted_kwh)
                threshold_kwh = regional_thresholds[region_name]

                if predicted_kwh <= threshold_kwh:
                    continue

                alert = build_peak_demand_alert(
                    forecast_date=forecast_date,
                    region_name=region_name,
                    predicted_kwh=predicted_kwh,
                    threshold_kwh=threshold_kwh,
                )

                cursor.execute("""
                    SELECT alert_key
                    FROM warehouse.fact_grid_alert
                    WHERE alert_type = %s
                      AND alert_date = %s
                      AND region_name = %s
                """, (
                    alert["alert_type"],
                    alert["alert_date"],
                    alert["region_name"],
                ))

                existing = cursor.fetchone()

                if existing:
                    skipped += 1
                    continue

                cursor.execute("""
                    INSERT INTO warehouse.fact_grid_alert (
                        alert_type,
                        severity,
                        alert_date,
                        region_name,
                        predicted_kwh,
                        threshold_kwh,
                        trigger_reason,
                        status,
                        created_at
                    )
                    VALUES (
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, CURRENT_TIMESTAMP
                    )
                """, (
                    alert["alert_type"],
                    alert["severity"],
                    alert["alert_date"],
                    alert["region_name"],
                    alert["predicted_kwh"],
                    alert["threshold_kwh"],
                    alert["trigger_reason"],
                    alert["status"],
                ))

                inserted += 1

        connection.commit()

        print("Peak-demand alert generation completed.")
        print(f"Forecast rows evaluated: {len(forecasts)}")
        print(f"Regions evaluated: {len(regional_thresholds)}")
        print(f"Alerts inserted: {inserted}")
        print(f"Existing alerts skipped: {skipped}")

        for region, threshold in sorted(regional_thresholds.items()):
            print(f"{region}: threshold={threshold:.2f} kWh")

    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


if __name__ == "__main__":
    generate_peak_demand_alerts()
