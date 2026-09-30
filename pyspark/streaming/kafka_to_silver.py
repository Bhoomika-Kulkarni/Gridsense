from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json
from pyspark.sql.types import (
    DoubleType,
    StringType,
    StructField,
    StructType,
)


# Create Spark session
spark = (
    SparkSession.builder
    .appName("GridSenseKafkaToSilver")
    .master("local[2]")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")


# Kafka event schema
event_schema = StructType([
    StructField("meter_id", StringType(), True),
    StructField("customer_id", StringType(), True),
    StructField("region", StringType(), True),
    StructField("timestamp", StringType(), True),
    StructField("kwh", DoubleType(), True),
    StructField("event_type", StringType(), True),
])


# Read streaming data from Kafka
kafka_stream = (
    spark.readStream
    .format("kafka")
    .option("kafka.bootstrap.servers", "kafka:29092")
    .option("subscribe", "grid_meter_events")
    .option("startingOffsets", "earliest")
    .load()
)


# Convert Kafka value from binary to JSON
parsed_stream = (
    kafka_stream
    .selectExpr("CAST(value AS STRING) AS json_value")
    .select(from_json(col("json_value"), event_schema).alias("event"))
    .select("event.*")
)


# Silver streaming output location
output_path = "data/silver/streaming_meter_events"

# Checkpoint location
checkpoint_path = "data/silver/checkpoints/meter_events"


# Write transformed streaming data
query = (
    parsed_stream
    .writeStream
    .format("json")
    .outputMode("append")
    .option("path", output_path)
    .option("checkpointLocation", checkpoint_path)
    .trigger(once=True)
    .start()
)


query.awaitTermination()

print("Kafka to Silver streaming transformation completed.")

spark.stop()