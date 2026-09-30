SELECT
    region_key,
    region_name,
    created_at
FROM {{ source('warehouse', 'dim_region') }}
  