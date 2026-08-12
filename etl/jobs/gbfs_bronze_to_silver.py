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

def _get_optional_arg(arg_name: str, default_value=None):
    """Retrieves an optional Glue argument if passed in sys.argv, otherwise returns default_value."""
    if f"--{arg_name}" in sys.argv:
        return getResolvedOptions(sys.argv, [arg_name])[arg_name]
    return default_value

def _process_station_status():
    BRONZE_STATION_STATUS_S3_PATH = f"s3://{DATA_LAKE_BUCKET}/bronze/gbfs/station_status/*/*/*/*.json"
    SILVER_STATION_STATUS_S3_PATH = f"s3://{DATA_LAKE_BUCKET}/silver/station_status/"

def _process_station_info():
    SILVER_STATION_INFO_S3_PATH = f"s3://{DATA_LAKE_BUCKET}/silver/station_info/"

    optional_rerun_paths = _get_optional_arg("RERUN_PATHS") # ex. bronze/gbfs/station_info/year=2026/month=08/day=11/
    if optional_rerun_paths is not None:
        rerun_paths = optional_rerun_paths.split(",")

        if not any(["station_info" in path for path in rerun_paths]):
            logger.error("No rerun path for station_info found.")
            raise RuntimeError(f"Processing station_info rerun without any rerun paths from station_info bucket. Rerun paths: {optional_rerun_paths}")

        rerun_path = next((path for path in rerun_paths if "station_info" in path), None)
        bronze_station_info_s3_path = f"s3://{DATA_LAKE_BUCKET}/{rerun_path}"
    else:
        bronze_station_info_s3_path = f"s3://{DATA_LAKE_BUCKET}/bronze/gbfs/station_info/"

    info_source = glueContext.create_dynamic_frame.from_options(
        connection_type="s3",
        connection_options={
            "paths": [bronze_station_info_s3_path],
            "recurse": True
        },
        format="json",
        format_options={"multiline": True},
        transformation_ctx="gbfs_bronze_to_silver_station_info_ctx"
    )

    station_info_df = info_source.toDF()
    if station_info_df.rdd.isEmpty():
        logger.info("No new station_info files to process.")
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
        col("station.long").cast(DoubleType()).alias("long"),
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