import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt

app = FastAPI(
    title="GridSense API",
    description="Real-time energy operations API",
    version="1.0.0"
)

FRONTEND_URL = os.getenv(
    "FRONTEND_URL",
    "http://localhost:5173"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        FRONTEND_URL
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
def get_database_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.getenv("DB_NAME", "gridsense"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD")
    )

SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY",
    "gridsense-development-secret-key"
)
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/login"
)

def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        username = payload.get("sub")

        if username is None:
            raise credentials_exception

        return {
            "username": username,
            "role": payload.get("role")
        }

    except JWTError:
        raise credentials_exception
def require_admin(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    return current_user

@app.get("/")
def root():
    return {
        "message": "GridSense API is running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }
@app.get("/api/alerts")
def get_alerts():
    connection = get_database_connection()

    try:
        query = """
            SELECT
                alert_key,
                alert_type,
                severity,
                alert_date,
                region_name,
                predicted_kwh,
                threshold_kwh,
                trigger_reason,
                status,
                created_at,
                acknowledged_at
            FROM warehouse.fact_grid_alert
            ORDER BY alert_date DESC, alert_key;
        """

        with connection.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()

        alerts = []

        for row in rows:
            alerts.append({
                "alert_key": row[0],
                "alert_type": row[1],
                "severity": row[2],
                "alert_date": row[3],
                "region_name": row[4],
                "predicted_kwh": float(row[5]) if row[5] is not None else None,
                "threshold_kwh": float(row[6]) if row[6] is not None else None,
                "trigger_reason": row[7],
                "status": row[8],
                "created_at": row[9],
                "acknowledged_at": row[10]
            })

        return {
            "count": len(alerts),
            "alerts": alerts
        }

    finally:
        connection.close()
@app.get("/api/load-forecast")
def get_load_forecast():
    connection = get_database_connection()

    try:
        query = """
            SELECT
                forecast_key,
                forecast_date,
                region_name,
                actual_kwh,
                predicted_kwh,
                model_name,
                mae,
                rmse,
                created_at
            FROM warehouse.fact_demand_forecast
            ORDER BY forecast_date, region_name;
        """

        with connection.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()

        forecasts = []

        for row in rows:
            forecasts.append({
                "forecast_key": row[0],
                "forecast_date": row[1],
                "region_name": row[2],
                "actual_kwh": float(row[3]),
                "predicted_kwh": float(row[4]),
                "model_name": row[5],
                "mae": float(row[6]) if row[6] is not None else None,
                "rmse": float(row[7]) if row[7] is not None else None,
                "created_at": row[8]
            })

        return {
            "count": len(forecasts),
            "forecasts": forecasts
        }

    finally:
        connection.close()    

@app.get("/api/dashboard")
def get_dashboard(current_user: dict = Depends(get_current_user)):
    connection = get_database_connection()

    try:
        query = """
            SELECT
                (SELECT COUNT(*) FROM warehouse.dim_customer) AS total_customers,
                (SELECT COUNT(*) FROM warehouse.dim_meter) AS total_meters,
                (SELECT COUNT(*) FROM warehouse.fact_energy_usage) AS total_energy_readings,
                (SELECT COUNT(*) FROM warehouse.fact_outage) AS total_outages,
                (SELECT COUNT(*)
                 FROM warehouse.fact_grid_alert
                 WHERE status = 'OPEN') AS open_alerts,
                (SELECT COUNT(*)
                 FROM warehouse.fact_grid_alert
                 WHERE status = 'RESOLVED') AS resolved_alerts,
                (SELECT COUNT(*) FROM warehouse.fact_demand_forecast) AS forecast_records,
                (SELECT COALESCE(SUM(kwh), 0)
                 FROM warehouse.fact_energy_usage) AS total_kwh;
        """

        with connection.cursor() as cursor:
            cursor.execute(query)
            row = cursor.fetchone()

        return {
            "total_customers": row[0],
            "total_meters": row[1],
            "total_energy_readings": row[2],
            "total_outages": row[3],
            "open_alerts": row[4],
            "resolved_alerts": row[5],
            "forecast_records": row[6],
            "total_kwh": float(row[7])
        }

    finally:
        connection.close()

@app.get("/api/regions/{id}")
def get_region(id: int):
    connection = get_database_connection()

    try:
        query = """
            SELECT
                r.region_key,
                r.region_name,

                (
                    SELECT COUNT(*)
                    FROM warehouse.dim_customer c
                    WHERE c.region_key = r.region_key
                ) AS customer_count,

                (
                    SELECT COUNT(*)
                    FROM warehouse.dim_meter m
                    WHERE m.region_key = r.region_key
                ) AS meter_count,

                (
                    SELECT COALESCE(SUM(e.kwh), 0)
                    FROM warehouse.fact_energy_usage e
                    INNER JOIN warehouse.dim_meter m
                        ON e.meter_key = m.meter_key
                    WHERE m.region_key = r.region_key
                ) AS total_kwh,

                (
                    SELECT COUNT(*)
                    FROM warehouse.fact_outage o
                    WHERE o.region_key = r.region_key
                ) AS outage_count

            FROM warehouse.dim_region r
            WHERE r.region_key = %s;
        """

        with connection.cursor() as cursor:
            cursor.execute(query, (id,))
            row = cursor.fetchone()

        if row is None:
            return {
                "error": "Region not found"
            }

        return {
            "region_key": row[0],
            "region_name": row[1],
            "customer_count": row[2],
            "meter_count": row[3],
            "total_kwh": float(row[4]),
            "outage_count": row[5]
        }

    finally:
        connection.close()

@app.get("/api/outages")
def get_outages():
    connection = get_database_connection()

    try:
        query = """
            SELECT
                outage_key,
                outage_id,
                asset_key,
                start_time,
                end_time,
                cause,
                region_key
            FROM warehouse.fact_outage
            ORDER BY start_time DESC;
        """

        with connection.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()

        outages = []

        for row in rows:
            outages.append({
                "outage_key": row[0],
                "outage_id": row[1],
                "asset_key": row[2],
                "start_time": row[3],
                "end_time": row[4],
                "cause": row[5],
                "region_key": row[6]
            })

        return {
            "count": len(outages),
            "outages": outages
        }

    finally:
        connection.close()

@app.get("/api/assets/risk")
def get_asset_risk():
    connection = get_database_connection()

    try:
        query = """
    SELECT
        a.asset_key,
        a.asset_id,
        r.region_name,
        a.capacity,
        a.status,
        (
            SELECT COUNT(*)
            FROM warehouse.fact_maintenance m
            WHERE m.asset_key = a.asset_key
        ) AS maintenance_count,
        (
            SELECT COUNT(*)
            FROM warehouse.fact_maintenance m
            WHERE m.asset_key = a.asset_key
              AND LOWER(m.status) NOT IN ('completed', 'closed')
        ) AS pending_maintenance_count,
        (
            SELECT COUNT(*)
            FROM warehouse.fact_maintenance m
            WHERE m.asset_key = a.asset_key
              AND m.scheduled_date < CURRENT_DATE
              AND LOWER(m.status) NOT IN ('completed', 'closed')
        ) AS overdue_maintenance_count
    FROM warehouse.dim_asset a
    INNER JOIN warehouse.dim_region r
        ON a.region_key = r.region_key
    ORDER BY a.asset_key;
    """

        with connection.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()

        assets = []

        for row in rows:
            maintenance_count = row[5]
            pending_count = row[6]
            overdue_count = row[7]

            risk_score = 0

            if str(row[4]).lower() not in ("active", "operational"):
                risk_score += 40

            if pending_count > 0:
                risk_score += 30

            if overdue_count > 0:
                risk_score += 30

            if risk_score >= 70:
                risk_level = "HIGH"
            elif risk_score >= 40:
                risk_level = "MEDIUM"
            else:
                risk_level = "LOW"

            if overdue_count > 0:
                recommendation = "Schedule maintenance immediately"
            elif pending_count > 0:
                recommendation = "Review pending maintenance work orders"
            elif str(row[4]).lower() not in ("active", "operational"):
                recommendation = "Inspect asset status"
            else:
                recommendation = "No immediate maintenance action"

            assets.append({
                "asset_key": row[0],
                "asset_id": row[1],
                "region_name": row[2],
                "capacity": float(row[3]),
                "status": row[4],
                "maintenance_count": row[5],
                "pending_maintenance_count": row[6],
                "overdue_maintenance_count": row[7],
                "risk_score": risk_score,
                "risk_level": risk_level,
                "recommendation": recommendation
            })

        return {
            "count": len(assets),
            "assets": assets
        }

    finally:
        connection.close()

@app.get("/api/grid/live")
def get_grid_live():
    connection = get_database_connection()

    try:
        query = """
            SELECT
                MAX(e.reading_timestamp) AS latest_reading_time,

                (
                    SELECT COALESCE(SUM(kwh), 0)
                    FROM warehouse.fact_energy_usage
                    WHERE reading_timestamp = (
                        SELECT MAX(reading_timestamp)
                        FROM warehouse.fact_energy_usage
                    )
                ) AS current_load_kwh,

                (
                    SELECT COALESCE(SUM(kwh), 0)
                    FROM warehouse.fact_energy_usage
                    WHERE reading_timestamp::date = (
                        SELECT MAX(reading_timestamp)::date
                        FROM warehouse.fact_energy_usage
                    )
                ) AS today_energy_kwh,

                (
                    SELECT COUNT(DISTINCT meter_key)
                    FROM warehouse.fact_energy_usage
                    WHERE reading_timestamp = (
                        SELECT MAX(reading_timestamp)
                        FROM warehouse.fact_energy_usage
                    )
                ) AS active_meters

            FROM warehouse.fact_energy_usage e;
        """

        with connection.cursor() as cursor:
            cursor.execute(query)
            row = cursor.fetchone()

        regional_query = """
            SELECT
                r.region_key,
                r.region_name,
                COALESCE(SUM(e.kwh), 0) AS total_kwh
            FROM warehouse.fact_energy_usage e
            INNER JOIN warehouse.dim_region r
                ON e.region_key = r.region_key
            WHERE e.reading_timestamp = (
                SELECT MAX(reading_timestamp)
                FROM warehouse.fact_energy_usage
            )
            GROUP BY r.region_key, r.region_name
            ORDER BY r.region_key;
        """

        with connection.cursor() as cursor:
            cursor.execute(regional_query)
            regional_rows = cursor.fetchall()

        regional_load = []

        for regional_row in regional_rows:
            regional_load.append({
                "region_key": regional_row[0],
                "region_name": regional_row[1],
                "load_kwh": float(regional_row[2])
            })

        return {
            "latest_reading_time": row[0],
            "current_load_kwh": float(row[1]),
            "today_energy_kwh": float(row[2]),
            "active_meters": row[3],
            "regional_load": regional_load
        }

    finally:
        connection.close()

@app.get("/api/events/live")
def get_live_events():
    import json
    from pathlib import Path

    events_path = (
        Path(__file__).resolve().parents[2]
        / "data"
        / "silver"
        / "streaming_meter_events"
    )

    events = []

    try:
        json_files = sorted(events_path.glob("part-*.json"))

        for file_path in json_files:
            with open(file_path, "r", encoding="utf-8") as file:
                for line in file:
                    line = line.strip()

                    if not line:
                        continue

                    events.append(json.loads(line))

        events.sort(
            key=lambda event: event.get("timestamp", ""),
            reverse=True
        )

        return {
            "count": len(events),
            "events": events[:20]
        }

    except Exception as error:
        return {
            "count": 0,
            "events": [],
            "error": str(error)
        }

@app.post("/api/alerts/{id}/acknowledge")
def acknowledge_alert(
    id: int,
    current_user: dict = Depends(require_admin)
):
    connection = get_database_connection()

    try:
        query = """
            UPDATE warehouse.fact_grid_alert
            SET
                status = 'ACKNOWLEDGED',
                acknowledged_at = CURRENT_TIMESTAMP
            WHERE alert_key = %s
              AND status = 'OPEN'
            RETURNING
                alert_key,
                alert_type,
                severity,
                alert_date,
                region_name,
                status,
                acknowledged_at;
        """

        with connection.cursor() as cursor:
            cursor.execute(query, (id,))
            row = cursor.fetchone()

        if row is None:
            connection.rollback()

            return {
                "success": False,
                "message": "Alert not found or already acknowledged/resolved"
            }

        connection.commit()

        return {
            "success": True,
            "message": "Alert acknowledged successfully",
            "alert": {
                "alert_key": row[0],
                "alert_type": row[1],
                "severity": row[2],
                "alert_date": row[3],
                "region_name": row[4],
                "status": row[5],
                "acknowledged_at": row[6]
            }
        }

    finally:
        connection.close()

@app.get("/api/forecasts")
def get_forecasts():
    connection = get_database_connection()

    try:
        query = """
            SELECT
                forecast_key,
                forecast_date,
                region_name,
                actual_kwh,
                predicted_kwh,
                model_name,
                mae,
                rmse,
                created_at
            FROM warehouse.fact_demand_forecast
            ORDER BY forecast_date, region_name;
        """

        with connection.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()

        forecasts = []

        for row in rows:
            forecasts.append({
                "forecast_key": row[0],
                "forecast_date": row[1],
                "region_name": row[2],
                "actual_kwh": float(row[3]),
                "predicted_kwh": float(row[4]),
                "model_name": row[5],
                "mae": float(row[6]) if row[6] is not None else None,
                "rmse": float(row[7]) if row[7] is not None else None,
                "created_at": row[8]
            })

        return {
            "count": len(forecasts),
            "forecasts": forecasts
        }

    finally:
        connection.close()    

@app.get("/api/assets/risk")
def get_asset_risk():
    connection = get_database_connection()

    try:
        query = """
            SELECT
                a.asset_key,
                a.asset_id,
                r.region_name,
                a.capacity,
                a.status,

                (
                    SELECT COUNT(*)
                    FROM warehouse.fact_maintenance m
                    WHERE m.asset_key = a.asset_key
                ) AS maintenance_count,

                (
                    SELECT COUNT(*)
                    FROM warehouse.fact_maintenance m
                    WHERE m.asset_key = a.asset_key
                      AND LOWER(m.status) NOT IN ('completed', 'closed')
                ) AS pending_maintenance_count,

                (
                    SELECT COUNT(*)
                    FROM warehouse.fact_maintenance m
                    WHERE m.asset_key = a.asset_key
                      AND m.scheduled_date < CURRENT_DATE
                      AND LOWER(m.status) NOT IN ('completed', 'closed')
                ) AS overdue_maintenance_count

            FROM warehouse.dim_asset a

            INNER JOIN warehouse.dim_region r
                ON a.region_key = r.region_key

            ORDER BY a.asset_key;
        """

        with connection.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()

        assets = []

        for row in rows:
            maintenance_count = row[5]
            pending_count = row[6]
            overdue_count = row[7]

            risk_score = 0

            if str(row[4]).lower() not in ("active", "operational"):
                risk_score += 40

            if pending_count > 0:
                risk_score += 30

            if overdue_count > 0:
                risk_score += 30

            if risk_score >= 70:
                risk_level = "HIGH"
            elif risk_score >= 40:
                risk_level = "MEDIUM"
            else:
                risk_level = "LOW"

            if overdue_count > 0:
                recommendation = "Schedule maintenance immediately"
            elif pending_count > 0:
                recommendation = "Review pending maintenance work orders"
            elif str(row[4]).lower() not in ("active", "operational"):
                recommendation = "Inspect asset status"
            else:
                recommendation = "No immediate maintenance action"

            assets.append({
                "asset_key": row[0],
                "asset_id": row[1],
                "region_name": row[2],
                "capacity": float(row[3]),
                "status": row[4],
                "maintenance_count": maintenance_count,
                "pending_maintenance_count": pending_count,
                "overdue_maintenance_count": overdue_count,
                "risk_score": risk_score,
                "risk_level": risk_level,
                "recommendation": recommendation
            })

        return {
            "count": len(assets),
            "assets": assets
        }

    finally:
        connection.close()

@app.get("/api/data-quality")
def get_data_quality():
    connection = get_database_connection()

    try:
        checks = []

        with connection.cursor() as cursor:

            # 1. Energy usage null check
            cursor.execute("""
                SELECT COUNT(*)
                FROM warehouse.fact_energy_usage
                WHERE meter_key IS NULL
                   OR customer_key IS NULL
                   OR region_key IS NULL
                   OR reading_timestamp IS NULL
                   OR kwh IS NULL;
            """)
            null_energy = cursor.fetchone()[0]

            checks.append({
                "check_name": "Energy usage null values",
                "check_type": "NULL_CHECK",
                "failed_records": null_energy,
                "status": "PASS" if null_energy == 0 else "FAIL"
            })

            # 2. Duplicate meter readings
            cursor.execute("""
                SELECT COUNT(*)
                FROM (
                    SELECT
                        meter_key,
                        reading_timestamp,
                        COUNT(*) AS record_count
                    FROM warehouse.fact_energy_usage
                    GROUP BY meter_key, reading_timestamp
                    HAVING COUNT(*) > 1
                ) duplicates;
            """)
            duplicate_energy = cursor.fetchone()[0]

            checks.append({
                "check_name": "Duplicate meter readings",
                "check_type": "DUPLICATE_CHECK",
                "failed_records": duplicate_energy,
                "status": "PASS" if duplicate_energy == 0 else "FAIL"
            })

            # 3. Negative energy usage
            cursor.execute("""
                SELECT COUNT(*)
                FROM warehouse.fact_energy_usage
                WHERE kwh < 0;
            """)
            negative_energy = cursor.fetchone()[0]

            checks.append({
                "check_name": "Negative energy usage",
                "check_type": "RANGE_CHECK",
                "failed_records": negative_energy,
                "status": "PASS" if negative_energy == 0 else "FAIL"
            })

            # 4. Invalid customer references
            cursor.execute("""
                SELECT COUNT(*)
                FROM warehouse.fact_energy_usage f
                LEFT JOIN warehouse.dim_customer c
                    ON f.customer_key = c.customer_key
                WHERE c.customer_key IS NULL;
            """)
            invalid_customer = cursor.fetchone()[0]

            checks.append({
                "check_name": "Invalid customer references",
                "check_type": "REFERENTIAL_INTEGRITY",
                "failed_records": invalid_customer,
                "status": "PASS" if invalid_customer == 0 else "FAIL"
            })

            # 5. Invalid meter references
            cursor.execute("""
                SELECT COUNT(*)
                FROM warehouse.fact_energy_usage f
                LEFT JOIN warehouse.dim_meter m
                    ON f.meter_key = m.meter_key
                WHERE m.meter_key IS NULL;
            """)
            invalid_meter = cursor.fetchone()[0]

            checks.append({
                "check_name": "Invalid meter references",
                "check_type": "REFERENTIAL_INTEGRITY",
                "failed_records": invalid_meter,
                "status": "PASS" if invalid_meter == 0 else "FAIL"
            })

            # 6. Data freshness
            cursor.execute("""
                SELECT MAX(reading_timestamp)
                FROM warehouse.fact_energy_usage;
            """)
            latest_timestamp = cursor.fetchone()[0]

            checks.append({
                "check_name": "Energy data freshness",
                "check_type": "FRESHNESS_CHECK",
                "latest_record": latest_timestamp,
                "status": "PASS" if latest_timestamp is not None else "FAIL"
            })

            # 7. Energy record volume
            cursor.execute("""
                SELECT COUNT(*)
                FROM warehouse.fact_energy_usage;
            """)
            energy_count = cursor.fetchone()[0]

            checks.append({
                "check_name": "Energy record volume",
                "check_type": "VOLUME_CHECK",
                "record_count": energy_count,
                "status": "PASS" if energy_count > 0 else "FAIL"
            })

        passed = sum(
            1 for check in checks
            if check["status"] == "PASS"
        )

        failed = sum(
            1 for check in checks
            if check["status"] == "FAIL"
        )

        return {
            "overall_status": "PASS" if failed == 0 else "FAIL",
            "total_checks": len(checks),
            "passed_checks": passed,
            "failed_checks": failed,
            "checks": checks
        }

    finally:
        connection.close()

@app.post("/api/auth/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    admin_username = os.getenv("GRID_USERNAME", "admin")
    admin_password = os.getenv("GRID_PASSWORD", "gridsense123")

    operator_username = os.getenv(
        "GRID_OPERATOR_USERNAME",
        "operator"
    )
    operator_password = os.getenv(
        "GRID_OPERATOR_PASSWORD",
        "gridsense_operator"
    )

    if (
        form_data.username == admin_username
        and form_data.password == admin_password
    ):
        role = "admin"

    elif (
        form_data.username == operator_username
        and form_data.password == operator_password
    ):
        role = "operator"

    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_data = {
        "sub": form_data.username,
        "role": role
    }

    access_token = jwt.encode(
        token_data,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }