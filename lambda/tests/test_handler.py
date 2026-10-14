import io
import json
import os
from datetime import datetime, timezone

import boto3
import pytest
from moto import mock_aws
from pytest_mock import MockerFixture

# Set AWS environment variables prior to importing handler module
os.environ["AWS_ACCESS_KEY_ID"] = "testing"
os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
os.environ["AWS_SECURITY_TOKEN"] = "testing"
os.environ["AWS_SESSION_TOKEN"] = "testing"
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

os.environ["DATA_LAKE_BUCKET_NAME"] = "test-data-lake-bucket"
os.environ["DYNAMODB_TABLE_NAME"] = "test-citibike-table"
os.environ["LANGUAGE_CODE"] = "en"
os.environ["ENV_NAME"] = "local"
os.environ["USER_AGENT"] = "TestAgent/1.0"
os.environ["GBFS_DISCOVERY_URL"] = "http://mock-gbfs.com/gbfs.json"

from src import handler


class TestLambdaHandler:

    @pytest.fixture
    def aws_resources(self):
        """Setup mock S3 bucket and DynamoDB table"""
        with mock_aws():
            s3 = boto3.client("s3", region_name="us-east-1")
            s3.create_bucket(Bucket="test-data-lake-bucket")

            dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
            dynamodb.create_table(
                TableName="test-citibike-table",
                KeySchema=[{"AttributeName": "station_id", "KeyType": "HASH"}],
                AttributeDefinitions=[{"AttributeName": "station_id", "AttributeType": "S"}],
                BillingMode="PAY_PER_REQUEST"
            )

            # Re-bind module-level clients to the moto mock context
            handler.s3_client = s3
            handler.dynamodb_client = dynamodb

            yield {"s3": s3, "dynamodb": dynamodb}

    @pytest.fixture
    def fixed_now(self):
        """Fixed timestamp: 2026-09-01 12:00:00 UTC (Epoch: 1788264000)."""
        return datetime(2026, 9, 1, 12, 0, 0, tzinfo=datetime.UTC)

    def test_lambda_handler_status_happy_path(self, mocker: MockerFixture, aws_resources, fixed_now):
        """Test happy path execution for station status polling."""
        mocker.patch("src.handler.datetime", mocker.MagicMock(now=mocker.MagicMock(return_value=fixed_now)))

        mock_gbfs = mocker.patch("src.handler.GBFSClient")
        mock_gbfs_instance = mock_gbfs.return_value
        mock_gbfs_instance.fetch_station_status.return_value = {
            "data": {
                "stations": [
                    {"station_id": "id1", "num_bikes_available": 5, "num_docks_available": 3}
                ]
            }
        }

        mock_dynamo_service = mocker.patch("src.handler.DynamoDBService")
        mock_dynamo_service.return_value.update_station_status.return_value = 0

        event = {"poll_type": "status"}
        context = {}

        response = handler.lambda_handler(event, context)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["message"] == "Ingestion Succesful"
        assert body["poll_type"] == "status"
        assert body["payload_size"] == 1
        assert body["dynamo_error_count"] == 0
        assert body["s3_key"] == "bronze/gbfs/station_status/year=2026/month=09/day=01/hour=12/status_file_1788264000.json"

        # Verify object was written to S3 bucket
        s3_obj = aws_resources["s3"].get_object(
            Bucket="test-data-lake-bucket",
            Key=body["s3_key"]
        )
        saved_content = json.loads(s3_obj["Body"].read().decode("utf-8"))
        assert "data" in saved_content

    def test_lambda_handler_status_empty_payload(self, mocker: MockerFixture, aws_resources):
        """Test station status early return when API returns zero stations."""
        mock_gbfs = mocker.patch("src.handler.GBFSClient")
        mock_gbfs.return_value.fetch_station_status.return_value = {"data": {"stations": []}}

        event = {"poll_type": "status"}
        response = handler.lambda_handler(event, context={})

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["payload_size"] == 0
        assert "s3_key" not in body

    def test_lambda_handler_info_happy_path(self, mocker: MockerFixture, aws_resources, fixed_now):
        """Test happy path execution for station info polling."""
        mocker.patch("src.handler.datetime", mocker.MagicMock(now=mocker.MagicMock(return_value=fixed_now)))

        mock_gbfs = mocker.patch("src.handler.GBFSClient")
        mock_gbfs.return_value.fetch_station_info.return_value = {
            "data": {
                "stations": [
                    {"station_id": "id1", "name": "Central Park S", "capacity": 30}
                ]
            }
        }

        mock_dynamo = mocker.patch("src.handler.DynamoDBService")
        mock_dynamo.return_value.update_station_info.return_value = 0

        event = {"poll_type": "info"}
        response = handler.lambda_handler(event, context={})

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["poll_type"] == "info"
        assert body["payload_size"] == 1
        assert body["s3_key"] == "bronze/gbfs/station_info/year=2026/month=09/day=01/info_file_1788264000.json"

    def test_lambda_handler_trips_default_date_calculation(self, mocker: MockerFixture, aws_resources, fixed_now):
        """Test historical trips defaults to previous month processing when no rerun month is passed."""
        mocker.patch("src.handler.datetime", mocker.MagicMock(
            now=mocker.MagicMock(return_value=fixed_now),
            strptime=datetime.strptime
        ))

        mock_historical_client = mocker.patch("src.handler.CitiBikeHistoricalClient")
        client_instance = mock_historical_client.return_value
        
        # Mock extract_zip to return dummy bytes stream for both NYC and JC
        client_instance.extract_zip.return_value = io.BytesIO(b"fake_zip_bytes")
        client_instance.write_csvs_to_s3.return_value = 2

        event = {"poll_type": "trips"}
        response = handler.lambda_handler(event, context={})

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["zips_extracted"]["nyc"] == "https://s3.amazonaws.com/tripdata/202608-citibike-tripdata.zip"
        assert body["zips_extracted"]["jc"] == "https://s3.amazonaws.com/tripdata/JC-202608-citibike-tripdata.csv.zip"
        assert body["bronze_files_written"]["nyc"] == 2
        assert body["bronze_files_written"]["jc"] == 2

    def test_lambda_handler_trips_explicit_rerun_month(self, mocker: MockerFixture, aws_resources):
        """Test historical trips with an explicit YYYYMM rerun argument in the event payload."""
        mock_historical_client = mocker.patch("src.handler.CitiBikeHistoricalClient")
        client_instance = mock_historical_client.return_value
        client_instance.extract_zip.return_value = io.BytesIO(b"fake_zip_bytes")
        client_instance.write_csvs_to_s3.return_value = 1

        event = {"poll_type": "trips", "rerun_month": "202505"}
        response = handler.lambda_handler(event, context={})

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["zips_extracted"]["nyc"] == "https://s3.amazonaws.com/tripdata/202505-citibike-tripdata.zip"

    def test_lambda_handler_trips_failed_extraction_raises_runtime_error(self, mocker: MockerFixture, aws_resources):
        """Test that failure to extract zip archives for a city raises a RuntimeError."""
        mock_historical_client = mocker.patch("src.handler.CitiBikeHistoricalClient")
        client_instance = mock_historical_client.return_value
        # Fail zip extraction
        client_instance.extract_zip.return_value = None

        event = {"poll_type": "trips", "rerun_month": "202601"}

        with pytest.raises(RuntimeError, match="City nyc not extracted for either zip location"):
            handler.lambda_handler(event, context={})

    def test_lambda_handler_unrecognized_poll_type(self, aws_resources):
        """Test that an invalid or missing poll_type raises RuntimeError."""
        event = {"poll_type": "unknown_type"}

        with pytest.raises(RuntimeError, match="No execution available for poll_type: unknown_type"):
            handler.lambda_handler(event, context={})