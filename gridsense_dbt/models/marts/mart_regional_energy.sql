SELECT
    region_key,
    region_name,
    SUM(total_kwh) AS total_kwh,
    AVG(total_kwh) AS average_daily_kwh,
    MAX(total_kwh) AS peak_daily_kwh,
    SUM(reading_count) AS total_readings,
    AVG(active_meter_count) AS average_active_meters,
    AVG(active_customer_count) AS average_active_customers
FROM {{ ref('mart_daily_energy_usage') }}
GROUP BY
    region_key,
    region_name