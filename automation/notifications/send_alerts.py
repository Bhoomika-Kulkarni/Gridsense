import json
import os
import urllib.error
import urllib.request

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


def build_alert_message(alert):
    alert_key = alert[0]
    alert_type = alert[1]
    severity = alert[2]
    alert_date = alert[3]
    region_name = alert[4]
    predicted_kwh = alert[5]
    threshold_kwh = alert[6]
    trigger_reason = alert[7]

    return (
        f"🚨 GridSense Peak Demand Alert\n\n"
        f"Alert ID: {alert_key}\n"
        f"Alert Type: {alert_type}\n"
        f"Severity: {severity}\n"
        f"Region: {region_name}\n"
        f"Date: {alert_date}\n"
        f"Predicted Demand: {predicted_kwh:.2f} kWh\n"
        f"Alert Threshold: {threshold_kwh:.2f} kWh\n"
        f"Reason: {trigger_reason}"
    )


def notification_exists(connection, alert_key):
    query = """
        SELECT 1
        FROM warehouse.fact_alert_notification
        WHERE alert_key = %s
          AND notification_channel = 'SLACK'
        LIMIT 1;
    """

    with connection.cursor() as cursor:
        cursor.execute(query, (alert_key,))
        return cursor.fetchone() is not None


def send_slack_message(message):
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")

    if not webhook_url:
        raise RuntimeError(
            "SLACK_WEBHOOK_URL is not configured in the Airflow worker."
        )

    payload = json.dumps({
        "text": message
    }).encode("utf-8")

    request = urllib.request.Request(
        webhook_url,
        data=payload,
        headers={
            "Content-Type": "application/json"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            response_body = response.read().decode("utf-8")

        if response_body.strip() != "ok":
            raise RuntimeError(
                f"Slack webhook returned unexpected response: "
                f"{response_body}"
            )

        return True

    except urllib.error.HTTPError as error:
        error_body = error.read().decode(
            "utf-8",
            errors="replace"
        )

        raise RuntimeError(
            f"Slack webhook failed with HTTP {error.code}: "
            f"{error_body}"
        ) from error

    except urllib.error.URLError as error:
        raise RuntimeError(
            f"Unable to reach Slack webhook: {error.reason}"
        ) from error


def create_slack_notification(connection, alert):
    alert_key = alert[0]

    if notification_exists(connection, alert_key):
        print(
            f"Slack notification already exists: "
            f"alert={alert_key}"
        )
        return False

    message = build_alert_message(alert)

    print(
        f"Sending real Slack notification for alert {alert_key}..."
    )

    send_slack_message(message)

    print(
        f"Slack notification delivered successfully "
        f"for alert {alert_key}."
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
        VALUES (
            %s,
            'SLACK',
            'SENT',
            CURRENT_TIMESTAMP,
            %s,
            %s
        );
    """

    with connection.cursor() as cursor:
        cursor.execute(
            query,
            (
                alert_key,
                "#all-gridsense-alerts",
                message
            )
        )

    return True


if __name__ == "__main__":
    connection = get_database_connection()

    try:
        alerts = get_open_alerts(connection)

        print(f"Open alerts found: {len(alerts)}")

        processed_count = 0
        skipped_count = 0

        for alert in alerts:

            slack_created = create_slack_notification(
                connection,
                alert
            )

            if slack_created:
                processed_count += 1
            else:
                skipped_count += 1

            connection.commit()

        print(
            f"Slack notifications processed: "
            f"{processed_count}"
        )

        print(
            f"Slack notifications skipped: "
            f"{skipped_count}"
        )

        print(
            "Slack notification automation "
            "completed successfully."
        )

    except Exception as error:
        connection.rollback()
        print(f"Automation failed: {error}")
        raise

    finally:
        connection.close()