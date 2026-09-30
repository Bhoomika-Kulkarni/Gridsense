SELECT
    location AS region_name,
    DATE(reading_timestamp) AS weather_date,
    AVG(temperature) AS average_temperature,
    MAX(temperature) AS max_temperature,
    SUM(rainfall) AS total_rainfall,
    AVG(wind) AS average_wind,
    MAX(wind) AS max_wind
FROM {{ ref('stg_weather') }}
GROUP BY
    location,
    DATE(reading_timestamp)
ORDER BY
    weather_date,
    region_name