SELECT
    a.asset_key,
    a.asset_id,
    r.region_name,
    a.capacity,
    a.status AS asset_status,
    COUNT(m.maintenance_key) AS maintenance_count,
    COUNT(*) FILTER (WHERE m.status = 'Completed') AS completed_maintenance_count,
    COUNT(*) FILTER (WHERE m.status = 'Scheduled') AS scheduled_maintenance_count,
    COUNT(*) FILTER (WHERE m.status = 'In Progress') AS in_progress_maintenance_count
FROM {{ ref('stg_assets') }} AS a
INNER JOIN {{ ref('stg_regions') }} AS r
    ON a.region_key = r.region_key
LEFT JOIN {{ ref('stg_maintenance') }} AS m
    ON a.asset_key = m.asset_key
GROUP BY
    a.asset_key,
    a.asset_id,
    r.region_name,
    a.capacity,
    a.status