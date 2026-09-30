SELECT
    energy_usage_key,
    meter_key,
    customer_key,
    region_key,
    date_key,
    reading_timestamp,
    kwh,
    created_at
FROM {{ source('warehouse', 'fact_energy_usage') }}