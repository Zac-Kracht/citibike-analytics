import os

class Config:
    DATA_LAKE_BUCKET_NAME: str = os.environ["DATA_LAKE_BUCKET_NAME"]
    DYNAMODB_TABLE_NAME: str = os.environ["DYNAMODB_TABLE_NAME"]
    GBFS_DISCOVERY_URL: str = os.environ["GBFS_DISCOVERY_URL"]
    ENV_NAME: str = os.getenv("ENV_NAME", "dev")
    OWNER_CONTACT: str = os.getenv("OWNER_CONTACT", "")
    LANGUAGE_CODE: str = os.getenv("LANGUAGE_CODE", "en") # CitiBike GBFS supports en, fr, es