import boto3
import logging
import json

from datetime import datetime, timezone, timedelta

from src.config import Config
from src.gbfs_client import GBFSClient
from src.s3_service import S3Service
from src.dynamo_service import DynamoDBService
from src.citibike_historical_client import CitiBikeHistoricalClient

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client("s3")
dynamodb_client = boto3.resource("dynamodb")


def _handle_station_status(config: Config, event: dict):
    logger.info("Polling station_status data")

    gbfs_client = GBFSClient(
        config.GBFS_DISCOVERY_URL, 
        config.USER_AGENT,
        language_code=config.LANGUAGE_CODE
    )
    station_status_json = gbfs_client.fetch_station_status()
    stations = station_status_json.get("data", {}).get("stations", [])
    station_status_payload_size = len(stations)
    
    if station_status_payload_size == 0:
        logger.info("No stations to process")
        return {
            "payload_size": station_status_payload_size
        }

    now = datetime.now(timezone.utc)
    epoch_ts = int(now.timestamp())

    dynamo_service = DynamoDBService(
        dynamodb_client,
        config.DYNAMODB_TABLE_NAME
    )
    dynamo_service.update_station_status(stations, epoch_ts)

    partition_str = now.strftime("year=%Y/month=%m/day=%d/hour=%H")
    station_status_s3_key = f"bronze/gbfs/station_status/{partition_str}/status_file_{epoch_ts}.json"

    s3_service = S3Service(
        s3_client, 
        config.DATA_LAKE_BUCKET_NAME
    )
    s3_service.write_json_file(station_status_json, station_status_s3_key)

    return {
        "s3_key": station_status_s3_key,
        "payload_size": station_status_payload_size
    }


def _handle_station_info(config: Config, event: dict):
    logger.info("Polling station_info data")

    gbfs_client = GBFSClient(
        config.GBFS_DISCOVERY_URL, 
        config.USER_AGENT,
        language_code=config.LANGUAGE_CODE,
    )
    station_info_json = gbfs_client.fetch_station_info()
    stations = station_info_json.get("data", {}).get("stations", [])
    station_info_payload_size = len(stations)

    if station_info_payload_size == 0:
        logger.info("No stations to process")
        return {
            "payload_size": station_info_payload_size
        }

    now = datetime.now(timezone.utc)
    epoch_ts = int(now.timestamp())

    dynamo_service = DynamoDBService(
        dynamodb_client,
        config.DYNAMODB_TABLE_NAME
    )
    dynamo_service.update_station_info(stations, epoch_ts)

    partition_str = now.strftime("year=%Y/month=%m/day=%d")
    station_info_s3_key = f"bronze/gbfs/station_info/{partition_str}/info_file_{epoch_ts}.json"

    s3_service = S3Service(
        s3_client, 
        config.DATA_LAKE_BUCKET_NAME
    )
    s3_service.write_json_file(station_info_json, station_info_s3_key)

    return {
        "s3_key": station_info_s3_key,
        "payload_size": station_info_payload_size
    }

def _handle_historical_trips(config: Config, event: dict):
    rerun_arg = event.get("rerun_month", None) # Only for trips reruns, format: YYYYMM
    if rerun_arg:
        month_to_process = datetime.strptime(rerun_arg, "%Y%m")
    else:
        month_to_process = datetime.now().replace(day=1) - timedelta(days=1)

    file_key = month_to_process.strftime("%Y%m")
    bronze_s3_prefix = f"bronze/trips/year={month_to_process.year}/month={month_to_process.month}"

    s3_service = S3Service(
        s3_client, 
        config.DATA_LAKE_BUCKET_NAME
    )

    citibike_historical_client = CitiBikeHistoricalClient(
        s3_service,
        config.USER_AGENT
    )

    results = {
        "zips_extracted": {},
        "bronze_files_written": {}
    }

    # Conflicting filenames for NYC vs JC
    urls_to_process = { 
        "nyc": [
            f"https://s3.amazonaws.com/tripdata/{file_key}-citibike-tripdata.zip",
            f"https://s3.amazonaws.com/tripdata/{file_key}-citibike-tripdata.csv.zip"
        ],
        "jc": [
            f"https://s3.amazonaws.com/tripdata/JC-{file_key}-citibike-tripdata.csv.zip",
            f"https://s3.amazonaws.com/tripdata/JC-{file_key}-citibike-tripdata.zip"
        ]
    }

    for city, urls in urls_to_process.items():
        city_complete = False
        for zip_url in urls:
            zip_buffer = citibike_historical_client.extract_zip(zip_url)
            if not zip_buffer:
                continue

            file_count = citibike_historical_client.write_csvs_to_s3(zip_buffer, bronze_s3_prefix)
            if file_count > 0:
                # Only use one successful extraction per city 
                logger.info(f"Successfully wrote bronze trips data for city {city}")
                city_complete = True
                results["zips_extracted"][city] = zip_url
                results["bronze_files_written"][city] = file_count
                break

        # Raise error if no locations for a city are successfully extracted
        if not city_complete:
            raise RuntimeError(f"City {city} not extracted for either zip location: {urls_to_process[city]}")

    # Write _SUCCESS file only when both cities process successfully
    s3_service.write_success_file(f"{bronze_s3_prefix}")

    return results


def lambda_handler(event, context):
    # Load configs
    config = Config()
    poll_type = event.get("poll_type", None)

    allowed_poll_types = {
        "status": _handle_station_status,
        "info": _handle_station_info,
        "trips": _handle_historical_trips
    }

    logger.info(f"Loaded lambda configs | Poll Type: {poll_type}")

    # Determine handler function based on lambda event
    if poll_type in allowed_poll_types:
        handle_func = allowed_poll_types.get(poll_type)
        result = handle_func(config, event)
    else:
        logger.error(f"Poll type {poll_type} unrecognized")
        raise RuntimeError(f"No execution available for poll_type: {poll_type}")  

    # Return results
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Ingestion Succesful",
            "poll_type": poll_type,
            "env": config.ENV_NAME,
            **result
        })
    }
