import sys
import logging

from awsglue.utils import getResolvedOptions
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.context import SparkContext
from pyspark.sql.functions import when
from concurrent.futures import ThreadPoolExecutor, as_completed


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
DATA_TO_PROCESS = args["DATA_TO_PROCESS"].upper()

def get_optional_arg(arg_name: str, default_value=None):
    """Retrieves an optional Glue argument if passed in sys.argv, otherwise returns default_value."""
    if f"--{arg_name}" in sys.argv:
        return getResolvedOptions(sys.argv, [arg_name])[arg_name]
    return default_value

def process_station_status():
    BRONZE_STATION_STATUS_S3_PATH = f"s3://{DATA_LAKE_BUCKET}/bronze/gbfs/station_status/*/*/*/*.json"
    SILVER_STATION_STATUS_S3_PATH = f"s3://{DATA_LAKE_BUCKET}/silver/station_status/"

def process_station_info():
    BRONZE_STATION_INFO_S3_PATH = f"s3://{DATA_LAKE_BUCKET}/bronze/gbfs/station_info/*/*/*/*.json"
    SILVER_STATION_INFO_S3_PATH = f"s3://{DATA_LAKE_BUCKET}/silver/station_info/"

def main():
    data_flow_registry = {
        "STATION_STATUS": process_station_status,
        "STATION_INFO": process_station_info
    }

    # Select processing functions based on --DATA_TO_PROCESS param
    if DATA_TO_PROCESS == "ALL":
        selected_flows = data_flow_registry
    elif DATA_TO_PROCESS in data_flow_registry:
        selected_flows = {DATA_TO_PROCESS: data_flow_registry[DATA_TO_PROCESS]}
    else:
        valid_options = ["ALL"] + list(data_flow_registry.keys())
        raise ValueError(
            f"Invalid --DATA_TO_PROCESS value '{DATA_TO_PROCESS}'. Must be one of: {valid_options}"
        )

    logger.info(f"Executing target flow(s): {list(selected_flows.keys())}")

    errors = []

    # If running a single flow, run sequentially. If ALL, run concurrently
    if len(selected_flows) == 1:
        flow_name, flow_func = list(selected_flows.items())[0]
        try:
            flow_func()
        except Exception as e:
            logger.error(f"Error encountered in {flow_name}: {str(e)}", exc_info=True)
            errors.append((flow_name, e))
    else:
        with ThreadPoolExecutor(max_workers=len(selected_flows)) as executor:
            futures = {
                executor.submit(func): name
                for name, func in selected_flows.items()
            }

            for future in as_completed(futures):
                flow_name = futures[future]
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Error encountered in {flow_name}: {str(e)}", exc_info=True)
                    errors.append((flow_name, e))

    if errors:
        failed_flows = ", ".join([f[0] for f in errors])
        raise RuntimeError(f"Job failed because the following flow(s) encountered errors: {failed_flows}")

    job.commit()
    logger.info("GBFS Bronze to Silver Glue Job completed successfully.")

if __name__ == "__main__":
    main()