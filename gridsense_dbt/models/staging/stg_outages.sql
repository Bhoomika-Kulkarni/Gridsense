SELECT
    outage_key,
    outage_id,
    asset_key,
    region_key,
    start_date_key,
    end_date_key,
    start_time,
    end_time,
    duration_minutes,
    cause,
    created_at
FROM {{ source('warehouse', 'fact_outage') }}