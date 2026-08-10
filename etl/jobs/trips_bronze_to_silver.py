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
from datetime import datetime


logger = logging.getLogger()
logger.setLevel(logging.INFO)

args = getResolvedOptions(sys.argv, ["JOB_NAME", "DATA_LAKE_BUCKET", "ENV_NAME"])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args["JOB_NAME"], args)

spark.conf.set("spark.sql.parquet.fs.optimized.committer.optimization-enabled", "true")
spark.conf.set("spark.sql.sources.partitionOverwriteMode", "dynamic")

# Enable Hadoop s3a for public S3 bucket access
hadoop_conf = sc._jsc.hadoopConfiguration()
hadoop_conf.set(
    "fs.sa.aws.credentials.provider",
    "org.apache.hadoop.fs.s3a.AnonymousAWSCredentialsProvider"
)

DATA_LAKE_BUCKET = args["DATA_LAKE_BUCKET"]

def get_optional_arg(arg_name: str, default_value=None):
    """Retrieves an optional Glue argument if passed in sys.argv, otherwise returns default_value."""
    if f"--{arg_name}" in sys.argv:
        return getResolvedOptions(sys.argv, [arg_name])[arg_name]
    return default_value

def resolve_file_date():
    optional_month_to_process = get_optional_arg("MONTH_TO_PROCESS") # Optional arg for rerunning previous months

    if optional_month_to_process is not None:
        run_date = datetime.strptime(optional_month_to_process, "%Y%m")
        file_year = run_date.year
        file_month = run_date.month
    else:
        run_date = datetime.now()
        file_year = run_date.year
        file_month = run_date.month - 1
        if file_month == 0:
            file_year -= 1
            file_month = 12

    file_year_str = f"{file_year}"
    file_month_str = f"0{file_month}" if file_month < 10 else f"{file_month}"

    return file_year_str, file_month_str

def process_raw_data(s3_path: str, region_name: str):
    logger.info(f"Attempting to extract data from: {s3_path}")

    try:
        df = (
            spark.read.option("header", "true")
            .option("inferSchema", "false")
            .csv(s3_path)
        )
    except Exception as e:
        logger.warn(f"Failed to extract data from file {s3_path}. Details: {e}")
        return None

    # Remove nulls from non-nullable fields
    df = df.dropna(
        subset=["ride_id", "started_at", "ended_at", "start_station_id", "end_station_id", "start_lat", "start_lng", "end_lat", "end_lng"]
    )

    # Convert to correct datatypes
    df = (
        df.withColumn("started_at", to_timestamp("started_at"))
        .withColumn("ended_at", to_timestamp("ended_at"))
        .withColumn("start_lat", col("start_lat").cast(DoubleType()))
        .withColumn("start_lng", col("start_lng").cast(DoubleType()))
        .withColumn("end_lat", col("end_lat").cast(DoubleType()))
        .withColumn("end_lng", col("end_lng").cast(DoubleType()))
        .withColumn("duration_seconds", unix_timestamp("ended_at") - unix_timestamp("started_at"))
    )

    # Filter invalid trip durations
    df = df.filter(
        (col("duration_seconds") >= 60)
        & (col("duration_seconds") <= 86400)
    )

    # Partition cols
    df = (
        df.withColumn("year", year("started_at"))
        .withColumn("month", month("started_at"))
    )

    # Final columns
    df = df.select(
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

    return df


def process_monthly_trips():
    SILVER_TRIPS_S3_PATH = f"s3://{DATA_LAKE_BUCKET}/silver/trips/"

    file_year, file_month = resolve_file_date()
    file_key = f"{file_year}{file_month}"

    logger.info(f"Processing YYYYMM = {file_key}")

    # Conflicting filenames for NYC vs JC
    nyc_paths = [
        f"s3a://tripdata/{file_key}-citibike-tripdata.zip",
        f"s3a://tripdata/{file_key}-citibike-tripdata.csv.zip"
    ]
    jc_paths = [
        f"s3a://tripdata/JC-{file_key}-citibike-tripdata.csv.zip",
        f"s3a://tripdata/JC-{file_key}-citibike-tripdata.zip"
    ]

    nyc_df = None
    for path in nyc_paths:
        nyc_df = process_raw_data(path)
        if nyc_df is not None:
            break

    jc_df = None
    for path in jc_paths:
        jc_df = process_raw_data(path)
        if jc_df is not None:
            break

    if nyc_df is not None and jc_df is not None:
        logger.info("Unioning NYC and JC trip data...")
        combined_df = nyc_df.unionByName(jc_df, allowMissingColumns=True)
    elif nyc_df is not None:
        logger.info("Only found NYC file")
        combined_df = nyc_df
    elif jc_df is not None:
        logger.info("Only found JC file")
        combined_df = jc_df
    else:
        logger.error("Failed to find both files")
        raise RuntimeError(f"Failed to load both NYC and JC files for YYYYMM: {file_key}")

    logger.info(f"Writing combined silver parquet to: {SILVER_TRIPS_S3_PATH}")

    (
        combined_df.repartition("year", "month")
        .write.mode("overwrite")
        .partitionBy("year", "month")
        .parquet(SILVER_TRIPS_S3_PATH)
    )


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