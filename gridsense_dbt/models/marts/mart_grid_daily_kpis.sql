SELECT
    e.date_key,
    e.full_date,
    e.region_key,
    e.region_name,

    e.total_kwh,
    e.average_kwh,
    e.peak_meter_kwh,
    e.reading_count,
    e.active_meter_count,
    e.active_customer_count,

    COALESCE(o.outage_count, 0) AS outage_count,
    COALESCE(o.total_outage_minutes, 0) AS total_outage_minutes,
    COALESCE(o.average_outage_minutes, 0) AS average_outage_minutes,
    COALESCE(o.affected_asset_count, 0) AS affected_asset_count

FROM {{ ref('mart_daily_energy_usage') }} AS e

LEFT JOIN (
    SELECT
        start_date_key AS date_key,
        region_key,
        COUNT(*) AS outage_count,
        SUM(duration_minutes) AS total_outage_minutes,
        AVG(duration_minutes) AS average_outage_minutes,
        COUNT(DISTINCT asset_key) AS affected_asset_count
    FROM {{ ref('stg_outages') }}
    GROUP BY
        start_date_key,
        region_key
) AS o
    ON e.date_key = o.date_key
    AND e.region_key = o.region_key