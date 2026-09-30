SELECT
    meter_key,
    meter_id,
    customer_key,
    region_key,
    meter_type,
    installation_date,
    status,
    created_at
FROM {{ source('warehouse', 'dim_meter') }}