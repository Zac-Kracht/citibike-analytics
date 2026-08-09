import boto3
import logging
import json

from datetime import datetime

from src.config import Config
from src.gbfs_client import GBFSClient
from src.s3_service import S3Service

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client("s3")

def lambda_handler(event, context):
    # Load configs
    config = Config()
    now = datetime.now()
    logger.info("Loaded lambda configs")

    # Call CitiBike GBFS endpoints station info and status data
    gbfs_client = GBFSClient(
        config.GBFS_DISCOVERY_URL, 
        language_code=config.LANGUAGE_CODE, 
        owner_contact=config.OWNER_CONTACT, 
        env=config.ENV_NAME
    )
    station_status_json = gbfs_client.fetch_station_status()
    station_info_json = gbfs_client.fetch_station_info()
    logger.info("Retrieved GBFS data")

    # TODO: Write updated station statuses to DynamoDB

    # Write raw json files to S3
    s3_service = S3Service(
        s3_client, 
        config.DATA_LAKE_BUCKET_NAME
    )
    epoch_ts = int(now.timestamp())
    partition_str = now.strftime("year=%Y/month=%m/day=%d/hour=%H")
    station_status_s3_key = f"bronze/gbfs/station_status/{partition_str}/status_file_{epoch_ts}.json"
    station_info_s3_key = f"bronze/gbfs/station_info/{partition_str}/info_file_{epoch_ts}.json"

    s3_service.write_json_file(station_status_json, station_status_s3_key)
    s3_service.write_json_file(station_info_json, station_info_s3_key)
    logger.info("Wrote JSON data to S3")

    # Gather session data for response payload
    station_status_payload_size = len(station_status_json.get("data", {}).get("stations", []))
    station_info_payload_size = len(station_info_json.get("data", {}).get("stations", []))

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Ingestion Succesful",
            "station_status_s3_key": station_status_s3_key,
            "station_status_payload_size": station_status_payload_size,
            "station_info_s3_key": station_info_s3_key,
            "station_info_payload_size": station_info_payload_size,
            "env": config.ENV_NAME
        })
    }