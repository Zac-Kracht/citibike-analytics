import logging
import io
import urllib.request
import zipfile

from typing import Any
from src.s3_service import S3Service


logger = logging.getLogger()
logger.setLevel(logging.INFO)

class CitiBikeHistoricalClient:
    def __init__(self, s3_service: S3Service, user_agent: str):
        self.s3_service = s3_service
        self.user_agent = user_agent

    def extract_zip(self, url: str):
        logger.info(f"Extracting zip from: {url}")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": self.user_agent})

            with urllib.request.urlopen(req, timeout=10) as response:
                return io.BytesIO(response.read())
        except Exception as e:
            # Try next file name on extract failure
            logger.info(f"Failed to extract zip from tripdata url: {url}")
            return None

    def write_csvs_to_s3(self, zip_buffer: Any, s3_prefix: str):
        try:
            with zipfile.ZipFile(zip_buffer) as z:
                count = 0
                for filename in z.namelist():
                    if filename.endswith(".csv") and not filename.startswith("__MACOSX"):
                        logger.info(f"Extracting {filename} to S3 Bronze...")
                        with z.open(filename) as csv_file:
                            s3_target_key = f"{s3_prefix}/{filename}"
                            self.s3_service.write_csv_file_object(csv_file, s3_target_key)
                        count += 1
            logger.info(f"Extracted {count} files to S3 prefix {s3_prefix}")
            return count
        except Exception as e:
            logger.info("CSV file extraction to S3 failed")
            return 0
            
