import os
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
import numpy as np


# --------------------------------------------------
# 1. PostgreSQL connection
# --------------------------------------------------

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "gridsense")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD")

database_url = URL.create(
    drivername="postgresql+psycopg2",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=int(DB_PORT),
    database=DB_NAME,
)

engine = create_engine(database_url)

# --------------------------------------------------
# 2. Read forecasting data from dbt mart
# --------------------------------------------------

query = """
SELECT
    full_date,
    region_name,
    total_kwh,
    average_kwh,
    peak_meter_kwh,
    reading_count,
    active_meter_count,
    active_customer_count
FROM warehouse.mart_forecasting_input
ORDER BY region_name, full_date
"""

df = pd.read_sql(query, engine)

print("Data loaded successfully.")
print("Rows:", len(df))
print("Columns:", list(df.columns))


# --------------------------------------------------
# 3. Prepare date features
# --------------------------------------------------

df["full_date"] = pd.to_datetime(df["full_date"])

df["day_of_week"] = df["full_date"].dt.dayofweek
df["day_of_month"] = df["full_date"].dt.day
df["month"] = df["full_date"].dt.month
df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)


# --------------------------------------------------
# 4. Create lag features
# --------------------------------------------------

df = df.sort_values(["region_name", "full_date"])

df["lag_1"] = (
    df.groupby("region_name")["total_kwh"]
    .shift(1)
)

df["lag_7"] = (
    df.groupby("region_name")["total_kwh"]
    .shift(7)
)

df["rolling_7"] = (
    df.groupby("region_name")["total_kwh"]
    .transform(lambda x: x.shift(1).rolling(7).mean())
)


# Remove rows where lag values are unavailable
df = df.dropna().reset_index(drop=True)


# --------------------------------------------------
# 5. Encode region
# --------------------------------------------------
df["region_name_original"] = df["region_name"]
df = pd.get_dummies(
    df,
    columns=["region_name"],
    dtype=int
)


# --------------------------------------------------
# 6. Define features and target
# --------------------------------------------------

feature_columns = [
    "average_kwh",
    "peak_meter_kwh",
    "reading_count",
    "active_meter_count",
    "active_customer_count",
    "day_of_week",
    "day_of_month",
    "month",
    "is_weekend",
    "lag_1",
    "lag_7",
    "rolling_7",
]

region_columns = [
    column
    for column in df.columns
    if column.startswith("region_name_")
    and column != "region_name_original"
]

feature_columns.extend(region_columns)

X = df[feature_columns]
y = df["total_kwh"]


# --------------------------------------------------
# 7. Time-based train/test split
# --------------------------------------------------

# Split data chronologically within each region
train_parts = []
test_parts = []

for region, region_data in df.groupby("region_name_original"):
    region_data = region_data.sort_values("full_date")

    split_index = int(len(region_data) * 0.8)

    train_parts.append(region_data.iloc[:split_index])
    test_parts.append(region_data.iloc[split_index:])

train_df = pd.concat(train_parts)
test_df = pd.concat(test_parts)

X_train = train_df[feature_columns]
X_test = test_df[feature_columns]

y_train = train_df["total_kwh"]
y_test = test_df["total_kwh"]

print("Training rows:", len(X_train))
print("Testing rows:", len(X_test))


# --------------------------------------------------
# 8. Train Random Forest model
# --------------------------------------------------

model = RandomForestRegressor(
    n_estimators=100,
    random_state=42,
    n_jobs=-1
)

model.fit(X_train, y_train)


# --------------------------------------------------
# 9. Generate predictions
# --------------------------------------------------

predictions = model.predict(X_test)


# --------------------------------------------------
# 10. Evaluate model
# --------------------------------------------------

mae = mean_absolute_error(y_test, predictions)

rmse = np.sqrt(
    mean_squared_error(y_test, predictions)
)

print("\nModel Evaluation")
print("----------------")
print("MAE :", round(mae, 2))
print("RMSE:", round(rmse, 2))


# --------------------------------------------------
# 11. Display sample predictions
# --------------------------------------------------

results = test_df[
    ["full_date", "region_name_original", "total_kwh"]
].copy()

results = results.rename(
    columns={"region_name_original": "region_name"}
)

results["predicted_kwh"] = predictions

print("\nSample Forecast Results")
print("-----------------------")
print(results.head(10).to_string(index=False))

# Save forecast results to PostgreSQL

results["model_name"] = "RandomForestRegressor"
results["mae"] = mae
results["rmse"] = rmse

insert_query = text("""
    INSERT INTO warehouse.fact_demand_forecast
    (
        forecast_date,
        region_name,
        actual_kwh,
        predicted_kwh,
        model_name,
        mae,
        rmse
    )
    VALUES
    (
        :forecast_date,
        :region_name,
        :actual_kwh,
        :predicted_kwh,
        :model_name,
        :mae,
        :rmse
    )
""")

with engine.begin() as connection:
    for _, row in results.iterrows():
        connection.execute(
            insert_query,
            {
                "forecast_date": row["full_date"].date(),
                "region_name": row["region_name"],
                "actual_kwh": row["total_kwh"],
                "predicted_kwh": row["predicted_kwh"],
                "model_name": row["model_name"],
                "mae": row["mae"],
                "rmse": row["rmse"],
            }
        )

print("\nForecast results saved to PostgreSQL successfully.")
