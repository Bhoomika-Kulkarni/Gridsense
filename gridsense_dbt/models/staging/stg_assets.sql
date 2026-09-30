SELECT
    asset_key,
    asset_id,
    region_key,
    capacity,
    status,
    created_at
FROM {{ source('warehouse', 'dim_asset') }}