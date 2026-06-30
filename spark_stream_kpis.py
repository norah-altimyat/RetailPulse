import os

os.environ["SPARK_LOCAL_IP"] = "127.0.0.1"
os.environ["PYSPARK_PYTHON"] = r"C:\Users\noraf\anaconda3\python.exe"

from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, sum, count, round
from pyspark.sql.types import StructType, StringType, DoubleType, IntegerType

spark = SparkSession.builder \
    .appName("RetailPulseKPIs") \
    .master("local[*]") \
    .config("spark.hadoop.io.native.lib.available", "false") \
    .config("spark.sql.streaming.checkpointLocation", "file:///C:/spark_checkpoints/retailpulse_csv") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

schema = StructType() \
    .add("order_id", StringType()) \
    .add("product_id", StringType()) \
    .add("country", StringType()) \
    .add("price", DoubleType()) \
    .add("quantity", IntegerType()) \
    .add("event_time", StringType())

df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", "retail-events") \
    .option("startingOffsets", "latest") \
    .load()

json_df = df.selectExpr("CAST(value AS STRING)") \
    .select(from_json(col("value"), schema).alias("data")) \
    .select("data.*") \
    .withColumn("revenue", col("price") * col("quantity"))

kpis_by_country = json_df.groupBy("country") \
    .agg(
        round(sum("revenue"), 2).alias("total_revenue"),
        count("order_id").alias("total_orders"),
        round(sum("revenue") / count("order_id"), 2).alias("avg_order_value")
    )

def save_to_csv(batch_df, batch_id):
    output_dir = "output/kpis_by_country"
    output_file = os.path.join(output_dir, "latest_kpis.csv")

    os.makedirs(output_dir, exist_ok=True)

    pandas_df = batch_df.toPandas()
    pandas_df.to_csv(output_file, index=False)

    print(f"Batch {batch_id} saved to {output_file}")
    batch_df.show(truncate=False)


query = kpis_by_country.writeStream \
    .outputMode("complete") \
    .foreachBatch(save_to_csv) \
    .start()

query.awaitTermination()
