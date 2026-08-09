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

    def write_json_file(self, payload: dict, s3_key: str) -> bool:
        logger.info(f"Attempting S3 file upload at {s3_key}")
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