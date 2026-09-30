import pandas as pd
import numpy as np

from common import (
    load_config,
    initialize_random_seed,
    create_output_directories,
    get_project_root,
)


def generate_weather():
    config = load_config()
    initialize_random_seed(config)
    create_output_directories(config)

    regions = config["regions"]

    start_date = pd.Timestamp(config["date_range"]["start_date"])
    end_date = pd.Timestamp(config["date_range"]["end_date"])

    timestamps = pd.date_range(
        start=start_date,
        end=end_date + pd.Timedelta(days=1) - pd.Timedelta(hours=1),
        freq="1h"
    )

    weather = []

    for region in regions:
        for timestamp in timestamps:

            base_temperature = {
                "North": 24,
                "South": 28,
                "East": 26,
                "West": 27,
                "Central": 25,
            }[region]

            temperature = np.random.normal(
                loc=base_temperature,
                scale=4
            )

            if np.random.random() < 0.15:
                rainfall = np.random.uniform(0.1, 30.0)
            else:
                rainfall = 0.0

            wind = np.random.uniform(2, 35)

            weather.append({
                "location": region,
                "timestamp": timestamp,
                "temperature": round(temperature, 2),
                "rainfall": round(rainfall, 2),
                "wind": round(wind, 2),
            })

    df = pd.DataFrame(weather)

    df = df.sort_values(
        ["location", "timestamp"]
    ).reset_index(drop=True)

    output_dir = (
        get_project_root()
        / config["output"]["weather"]
    )

    output_file = output_dir / "weather.csv"

    df.to_csv(output_file, index=False)

    print("Weather dataset generated successfully.")
    print("Rows:", len(df))
    print("Columns:", list(df.columns))
    print("Output:", output_file)


if __name__ == "__main__":
    generate_weather()