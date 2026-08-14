import sys
import logging

from awsglue.utils import getResolvedOptions
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.context import SparkContext
from pyspark.sql.functions import (
    to_timestamp, col, unix_timestamp, 
    year, month
)
from pyspark.sql.types import DoubleType


logger = logging.getLogger()
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

args = getResolvedOptions(sys.argv, ["JOB_NAME", "DATA_LAKE_BUCKET", "ENV_NAME"])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args["JOB_NAME"], args)

spark.conf.set("spark.sql.parquet.fs.optimized.committer.optimization-enabled", "true")
spark.conf.set("spark.sql.sources.partitionOverwriteMode", "dynamic")

DATA_LAKE_BUCKET = args["DATA_LAKE_BUCKET"]
SILVER_TRIPS_S3_PATH = f"s3://{DATA_LAKE_BUCKET}/silver/trips/"
GLUE_BOOKMARK_CTX = "trips_bronze_to_silver_ctx"


def _get_optional_arg(arg_name: str, default_value=None):
    """Retrieves an optional Glue argument if passed in sys.argv, otherwise returns default_value."""
    if f"--{arg_name}" in sys.argv:
        return getResolvedOptions(sys.argv, [arg_name])[arg_name]
    return default_value

def _get_data_source():
    bronze_s3_path = _get_optional_arg("RERUN_PATH", f"s3://{DATA_LAKE_BUCKET}/bronze/trips/") # ex. bronze/trips/year=2026/month=08/

    return glueContext.create_dynamic_frame.from_options(
        connection_type="s3",
        connection_options={
            "paths": [bronze_s3_path],
            "recurse": True
        },
        format="csv",
        format_options={"withHeader": True},
        transformation_ctx=GLUE_BOOKMARK_CTX
    )

def process_monthly_trips():
    trips_df = _get_data_source().toDF()

    if trips_df.rdd.isEmpty():
        logger.error("No new trips files to process")
        raise RuntimeError("No new bronze trips files to process.")

    # Remove nulls from non-nullable fields
    trips_df = trips_df.dropna(
        subset=["ride_id", "started_at", "ended_at", "start_station_id", "end_station_id", "start_lat", "start_lng", "end_lat", "end_lng"]
    )

    # Convert to correct datatypes
    trips_df = (
        trips_df.withColumn("started_at", to_timestamp("started_at"))
        .withColumn("ended_at", to_timestamp("ended_at"))
        .withColumn("start_lat", col("start_lat").cast(DoubleType()))
        .withColumn("start_lng", col("start_lng").cast(DoubleType()))
        .withColumn("end_lat", col("end_lat").cast(DoubleType()))
        .withColumn("end_lng", col("end_lng").cast(DoubleType()))
        .withColumn("duration_seconds", unix_timestamp("ended_at") - unix_timestamp("started_at"))
    )

    # Filter invalid trip durations
    trips_df = trips_df.filter(
        (col("duration_seconds") >= 60)
        & (col("duration_seconds") <= 86400)
    )

    # Partition cols
    trips_df = (
        trips_df.withColumn("year", year("started_at"))
        .withColumn("month", month("started_at"))
    )

    # Final columns
    trips_df = trips_df.select(
        "ride_id",
        "rideable_type",
        "started_at",
        "ended_at",
        "start_station_name",
        "start_station_id",
        "end_station_name",
        "end_station_id",
        "start_lat", 
        "start_lng", 
        "end_lat", 
        "end_lng",
        "member_casual",
        "duration_seconds",
        "year",
        "month"
    )

    trips_df.cache()
    count = trips_df.count()
    logger.info(f"Writing {count} rows for trips to {SILVER_TRIPS_S3_PATH}")
    trips_df.show(n=10, truncate=False)
    logger.info(f"Writing silver parquet to: {SILVER_TRIPS_S3_PATH}")

    trips_df.write.mode("append").partitionBy("year", "month").parquet(SILVER_TRIPS_S3_PATH)
    logger.info("Successfully wrote trips data to S3.")


def main():
    try:
        process_monthly_trips()
    except Exception as e:
        logger.error(f"Error encountered during ETL: {str(e)}", exc_info=True)
        raise e

    job.commit()
    logger.info("GBFS Bronze to Silver Glue Job completed successfully.")

if __name__ == "__main__":
    main()