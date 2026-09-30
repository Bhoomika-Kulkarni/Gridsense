import os
import psycopg2


def get_database_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.getenv("DB_NAME", "gridsense"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD")
    )


def get_open_alerts(connection):
    query = """
        SELECT
            alert_key,
            alert_type,
            severity,
            alert_date,
            region_name,
            predicted_kwh,
            threshold_kwh,
            trigger_reason
        FROM warehouse.fact_grid_alert
        WHERE status = 'OPEN'
        ORDER BY alert_date, region_name;
    """

    with connection.cursor() as cursor:
        cursor.execute(query)
        return cursor.fetchall()


def create_notification(connection, alert, channel, recipient):
    alert_key = alert[0]
    region_name = alert[4]
    predicted_kwh = alert[5]
    threshold_kwh = alert[6]
    alert_date = alert[3]

    message = (
        f"HIGH PEAK DEMAND ALERT: {region_name} predicted demand is "
        f"{predicted_kwh:.2f} kWh, exceeding the alert threshold of "
        f"{threshold_kwh:.2f} kWh on {alert_date}."
    )

    query = """
        INSERT INTO warehouse.fact_alert_notification
        (
            alert_key,
            notification_channel,
            notification_status,
            sent_at,
            recipient,
            message
        )
        SELECT %s, %s, %s, CURRENT_TIMESTAMP, %s, %s
        WHERE NOT EXISTS (
            SELECT 1
            FROM warehouse.fact_alert_notification
            WHERE alert_key = %s
              AND notification_channel = %s
        );
    """

    with connection.cursor() as cursor:
        cursor.execute(
            query,
            (
                alert_key,
                channel,
                "SENT",
                recipient,
                message,
                alert_key,
                channel
            )
        )


if __name__ == "__main__":
    connection = get_database_connection()

    try:
        alerts = get_open_alerts(connection)

        print(f"Open alerts found: {len(alerts)}")

        for alert in alerts:
            create_notification(
                connection,
                alert,
                "EMAIL",
                "grid-operations@gridsense.local"
            )

            create_notification(
                connection,
                alert,
                "SLACK",
                "#grid-operations"
            )

        connection.commit()

        print(
            f"Notifications processed: "
            f"{len(alerts) * 2}"
        )

    except Exception as error:
        connection.rollback()
        print(f"Automation failed: {error}")

    finally:
        connection.close()