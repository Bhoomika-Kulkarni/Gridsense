SELECT
    date_key,
    full_date,
    year,
    quarter,
    month,
    month_name,
    week,
    day,
    day_name,
    is_weekend,
    created_at
FROM {{ source('warehouse', 'dim_date') }}