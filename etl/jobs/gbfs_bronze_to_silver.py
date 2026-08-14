import sys
import logging

from awsglue.utils import getResolvedOptions
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.context import SparkContext
from pyspark.sql.functions import explode, col, timestamp_seconds, year, month
from pyspark.sql.types import StringType, DoubleType, IntegerType


logger = logging.getLogger()
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

args = getResolvedOptions(sys.argv, ["JOB_NAME", "DATA_LAKE_BUCKET", "DATA_TO_PROCESS", "ENV_NAME"])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args["JOB_NAME"], args)

spark.conf.set("spark.sql.parquet.fs.optimized.committer.optimization-enabled", "true")
spark.conf.set("spark.sql.sources.partitionOverwriteMode", "dynamic")

DATA_LAKE_BUCKET = args["DATA_LAKE_BUCKET"]
DATA_TO_PROCESS = args.get("DATA_TO_PROCESS", "ALL").upper()

SILVER_STATION_STATUS_S3_PATH = f"s3://{DATA_LAKE_BUCKET}/silver/station_status/"
SILVER_STATION_INFO_S3_PATH = f"s3://{DATA_LAKE_BUCKET}/silver/station_info/"

def _get_optional_arg(arg_name: str, default_value=None):
    """Retrieves an optional Glue argument if passed in sys.argv, otherwise returns default_value."""
    if f"--{arg_name}" in sys.argv:
        return getResolvedOptions(sys.argv, [arg_name])[arg_name]
    return default_value

def _get_data_source(data_key: str):
    optional_rerun_paths = _get_optional_arg("RERUN_PATHS") # ex. bronze/gbfs/station_status/year=2026/month=08/day=11/hour=05/
    if optional_rerun_paths:
        rerun_paths = optional_rerun_paths.split(",")

        if not any([data_key in path for path in rerun_paths]):
            logger.error(f"No rerun path for {data_key} found.")
            raise RuntimeError(f"Processing {data_key} rerun without any rerun paths from {data_key} bucket. Rerun paths: {optional_rerun_paths}")

        rerun_path = next((path for path in rerun_paths if data_key in path), None)
        bronze_s3_path = f"s3://{DATA_LAKE_BUCKET}/{rerun_path}"
    else:
        bronze_s3_path = f"s3://{DATA_LAKE_BUCKET}/bronze/gbfs/{data_key}/"

    return glueContext.create_dynamic_frame.from_options(
        connection_type="s3",
        connection_options={
            "paths": [bronze_s3_path],
            "recurse": True
        },
        format="json",
        format_options={"multiline": True},
        transformation_ctx=f"gbfs_bronze_to_silver_{data_key}_ctx"
    )

def _process_station_status():
    station_status = _get_data_source("station_status").toDF()

    if station_status.rdd.isEmpty():
        logger.info("No new station_source files to process")
        return

    logger.info("Processing new station_status file")

    station_status = station_status.select(
        explode("data.stations").alias("station"),
        timestamp_seconds("last_updated").alias("snapshot_timestamp")
    )  

    station_status = station_status.select(
        col("station.station_id").cast(StringType()).alias("station_id"),
        col("station.num_bikes_available").cast(IntegerType()).alias("num_bikes_available"),
        col("station.num_docks_available").cast(IntegerType()).alias("num_docks_available"),
        col("station.num_ebikes_available").cast(IntegerType()).alias("num_ebikes_available"),
        col("station.is_installed").cast(IntegerType()).alias("is_installed"),
        "snapshot_timestamp"
    )

    station_status = station_status.dropna(subset=["station_id", "num_bikes_available", "num_ebikes_available", "is_installed"])
    station_status = station_status.filter(col("is_installed") == 1)

    station_status = station_status.withColumn(
        "num_classic_bikes_available", col("num_bikes_available") - col("num_ebikes_available")
    )
    station_status = station_status.filter(col("num_classic_bikes_available") >= 0).drop("num_bikes_available")

    station_status = (
        station_status
        .withColumn("year", year("snapshot_timestamp"))
        .withColumn("month", month("snapshot_timestamp"))
    )

    station_status.cache()
    count = station_status.count()
    logger.info(f"Writing {count} rows for station_status to {SILVER_STATION_STATUS_S3_PATH}")
    station_status.show(n=10, truncate=False)

    station_status.write.mode("append").partitionBy("year", "month").parquet(SILVER_STATION_STATUS_S3_PATH)
    logger.info("Successfully wrote station_status data to S3.")


def _process_station_info():
    station_info_df = _get_data_source("station_info").toDF()

    if station_info_df.rdd.isEmpty():
        logger.info("No new station_info files to process")
        return

    logger.info("Processing new station_info file")

    station_info_df = station_info_df.select(
        explode("data.stations").alias("station"),
        timestamp_seconds("last_updated").alias("snapshot_timestamp")
    )    

    station_info_df = station_info_df.select(
        col("station.station_id").cast(StringType()).alias("station_id"),
        col("station.short_name").cast(StringType()).alias("short_name"),
        col("station.name").cast(StringType()).alias("station_name"),
        col("station.region_id").cast(StringType()).alias("region_id"),
        col("station.lat").cast(DoubleType()).alias("lat"),
        col("station.lon").cast(DoubleType()).alias("lon"),
        col("station.capacity").cast(IntegerType()).alias("capacity"),
        "snapshot_timestamp"
    )

    station_info_df = station_info_df.dropna(subset=["station_id", "short_name"])

    station_info_df = (
        station_info_df
        .withColumn("year", year("snapshot_timestamp"))
        .withColumn("month", month("snapshot_timestamp"))
    )

    station_info_df.cache()
    count = station_info_df.count()
    logger.info(f"Writing {count} rows for station_info to {SILVER_STATION_INFO_S3_PATH}")
    station_info_df.show(n=10, truncate=False)

    station_info_df.write.mode("append").partitionBy("year", "month").parquet(SILVER_STATION_INFO_S3_PATH)
    logger.info("Successfully wrote station_info data to S3.")


def main():
    data_flow_registry = {
        "STATION_STATUS": [_process_station_status],
        "STATION_INFO": [_process_station_info],
        "ALL": [_process_station_status, _process_station_info]
    }

    data_flow = data_flow_registry.get(DATA_TO_PROCESS)

    if data_flow is None:
        raise ValueError(
            f"Invalid --DATA_TO_PROCESS value '{DATA_TO_PROCESS}'. Must be one of: {list(data_flow.keys())}"
        )

    logger.info(f"Executing target flow(s): {data_flow}")

    for process_func in data_flow:
        process_func()

    job.commit()
    logger.info("GBFS Bronze to Silver Glue Job completed successfully.")

if __name__ == "__main__":
    main()