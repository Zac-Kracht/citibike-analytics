import os
import pytest

@pytest.fixture
def mock_config():
    os.environ["DATA_LAKE_BUCKET_NAME"] = "test_bucket"    
    os.environ["DYNAMODB_TABLE_NAME"] = "test_table"    

def test_lambda_handler_success(mock_config):
    # from src.handler import lambda_handler

    # response = lambda_handler({}, None)
    pass