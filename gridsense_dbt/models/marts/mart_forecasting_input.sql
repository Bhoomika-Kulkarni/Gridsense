SELECT
    full_date,
    region_name,
    total_kwh,
    average_kwh,
    peak_meter_kwh,
    reading_count,
    active_meter_count,
    active_customer_count
FROM {{ ref('mart_daily_energy_usage') }}
ORDER BY
    region_name,
    full_date