import sys

from awsglue.utils import getResolvedOptions
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.context import SparkContext

from src.citibike_etl.transformations.trips import transform_trips_bronze_to_silver
from src.citibike_etl.utils.logging import get_logger

logger = get_logger("trips_bronze_to_silver_etl")

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
    """Get source data as a DynamicFrame. Use optional arg RERUN_PATH to ingest specific partition, else all new files will be processed."""
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
    bronze_trips_df = _get_data_source().toDF()

    if bronze_trips_df.rdd.isEmpty():
        raise RuntimeError("No new bronze trips files to process.")

    silver_trips_df = transform_trips_bronze_to_silver(bronze_trips_df)

    silver_trips_df.cache()
    count = silver_trips_df.count()
    logger.info(f"Writing {count} rows for trips to {SILVER_TRIPS_S3_PATH}")
    silver_trips_df.show(n=10, truncate=False)
    logger.info(f"Writing silver parquet to: {SILVER_TRIPS_S3_PATH}")

    silver_trips_df.write.mode("append").partitionBy("year", "month").parquet(SILVER_TRIPS_S3_PATH)
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