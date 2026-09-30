SELECT
    e.date_key,
    d.full_date,
    e.region_key,
    r.region_name,
    SUM(e.kwh) AS total_kwh,
    AVG(e.kwh) AS average_kwh,
    MAX(e.kwh) AS peak_meter_kwh,
    COUNT(*) AS reading_count,
    COUNT(DISTINCT e.meter_key) AS active_meter_count,
    COUNT(DISTINCT e.customer_key) AS active_customer_count
FROM {{ ref('stg_energy_usage') }} AS e
INNER JOIN {{ ref('stg_dates') }} AS d
    ON e.date_key = d.date_key
INNER JOIN {{ ref('stg_regions') }} AS r
    ON e.region_key = r.region_key
GROUP BY
    e.date_key,
    d.full_date,
    e.region_key,
    r.region_name