SELECT
    weather_key,
    location,
    reading_timestamp,
    temperature,
    rainfall,
    wind,
    created_at
FROM {{ source('warehouse', 'fact_weather') }}