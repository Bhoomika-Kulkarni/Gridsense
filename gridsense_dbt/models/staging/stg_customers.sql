SELECT
    customer_key,
    customer_id,
    customer_name,
    tariff_key,
    region_key,
    created_at
FROM {{ source('warehouse', 'dim_customer') }}