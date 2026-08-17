import json
import logging

from botocore.exceptions import ClientError
from typing import Any

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class S3Service:
    def __init__(self, s3_client: Any, bucket_name: str):
        self.s3_client = s3_client
        self.bucket_name = bucket_name

    def write_json_file(self, payload: dict, s3_key: str):
        logger.info(f"Attempting S3 json file upload at {s3_key}")
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=json.dumps(payload),
                ContentType="application/json"
            )
            logger.info("File successfully uploaded")
        except ClientError as e:
            logger.error(f"Failed to write file to S3 key {s3_key}: {e}")
            raise e

    def write_csv_file_object(self, csv_file: Any, s3_key: str):
        logger.info(f"Attempting S3 csv file upload at {s3_key}")
        try:
            self.s3_client.upload_fileobj(
                Bucket=self.bucket_name,
                Key=s3_key,
                Fileobj=csv_file,
            )
            logger.info("File successfully uploaded")
        except Exception as e:
            logger.error(f"Failed to write file to S3 key {s3_key}: {e}")
            raise e

    def write_success_file(self, prefix: str):
        s3_key = f"{prefix}/_SUCCESS"

        logger.info(f"Writing _SUCCESS marker file to s3://{self.bucket_name}/{s3_key}")

        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=b"",
                ContentType="application/x-empty"
            )
        except ClientError as e:
            logger.error(f"Failed to write _SUCCESS file to S3 key {s3_key}: {e}")
            raise e
            
