SELECT
    maintenance_key,
    work_order_id,
    asset_key,
    region_key,
    scheduled_date_key,
    scheduled_date,
    status,
    created_at
FROM {{ source('warehouse', 'fact_maintenance') }}