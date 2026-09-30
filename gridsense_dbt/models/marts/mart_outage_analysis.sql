SELECT
    o.region_key,
    r.region_name,
    o.cause,
    COUNT(*) AS outage_count,
    SUM(o.duration_minutes) AS total_outage_minutes,
    AVG(o.duration_minutes) AS average_outage_minutes,
    MAX(o.duration_minutes) AS maximum_outage_minutes,
    COUNT(DISTINCT o.asset_key) AS affected_asset_count
FROM {{ ref('stg_outages') }} AS o
INNER JOIN {{ ref('stg_regions') }} AS r
    ON o.region_key = r.region_key
GROUP BY
    o.region_key,
    r.region_name,
    o.cause