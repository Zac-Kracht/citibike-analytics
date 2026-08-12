import boto3
import logging
import json

from datetime import datetime, timezone
from typing import Final

from src.config import Config
from src.gbfs_client import GBFSClient
from src.s3_service import S3Service

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client("s3")


def _handle_station_status(gbfs_client: GBFSClient, s3_service: S3Service):
    logger.info("Polling station_status data")

    station_status_json = gbfs_client.fetch_station_status()

    now = datetime.now(timezone.utc)
    epoch_ts = int(now.timestamp())
    partition_str = now.strftime("year=%Y/month=%m/day=%d/hour=%H")
    station_status_s3_key = f"bronze/gbfs/station_status/{partition_str}/status_file_{epoch_ts}.json"

    s3_service.write_json_file(station_status_json, station_status_s3_key)

    station_status_payload_size = len(station_status_json.get("data", {}).get("stations", []))
    return {
        "s3_key": station_status_s3_key,
        "payload_size": station_status_payload_size
    }


def _handle_station_info(gbfs_client: GBFSClient, s3_service: S3Service):
    logger.info("Polling station_info data")

    station_info_json = gbfs_client.fetch_station_info()

    now = datetime.now(timezone.utc)
    epoch_ts = int(now.timestamp())
    partition_str = now.strftime("year=%Y/month=%m/day=%d")
    station_info_s3_key = f"bronze/gbfs/station_info/{partition_str}/info_file_{epoch_ts}.json"

    s3_service.write_json_file(station_info_json, station_info_s3_key)

    station_info_payload_size = len(station_info_json.get("data", {}).get("stations", []))
    return {
        "s3_key": station_info_s3_key,
        "payload_size": station_info_payload_size
    }

def lambda_handler(event, context):
    # Load configs
    config = Config()
    poll_type = event.get("poll_type", None)
    allowed_poll_types = {
        "status": _handle_station_status,
        "info": _handle_station_info
    }

    logger.info(f"Loaded lambda configs | Poll Type: {poll_type}")

    gbfs_client = GBFSClient(
        config.GBFS_DISCOVERY_URL, 
        language_code=config.LANGUAGE_CODE, 
        owner_contact=config.OWNER_CONTACT, 
        env=config.ENV_NAME
    )
    s3_service = S3Service(
        s3_client, 
        config.DATA_LAKE_BUCKET_NAME
    )

    # Determine handler function based on lambda event
    if poll_type in allowed_poll_types:
        handle_func = allowed_poll_types.get(poll_type)
        result = handle_func(gbfs_client, s3_service)
    else:
        logger.error(f"Poll type {poll_type} unrecognized")
        raise RuntimeError(f"No execution available for poll_type: {poll_type}")

    # TODO: Write updated station data to DynamoDB    

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Ingestion Succesful",
            "poll_type": poll_type,
            "env": config.ENV_NAME,
            **result
        })
    }