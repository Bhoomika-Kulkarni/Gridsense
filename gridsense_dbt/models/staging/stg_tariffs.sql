SELECT
    tariff_key,
    tariff_name,
    created_at
FROM {{ source('warehouse', 'dim_tariff') }}