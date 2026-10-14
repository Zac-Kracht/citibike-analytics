import io
import json
import os

import boto3
import pytest
from botocore.exceptions import ClientError
from moto import mock_aws
from pytest_mock import MockerFixture

from src.s3_service import S3Service


class TestS3Service:

    @pytest.fixture
    def aws_credentials(self):
        """Mocked AWS Credentials for moto"""
        os.environ["AWS_ACCESS_KEY_ID"] = "testing"
        os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
        os.environ["AWS_SECURITY_TOKEN"] = "testing"
        os.environ["AWS_SESSION_TOKEN"] = "testing"
        os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

    @pytest.fixture
    def s3_client(self, aws_credentials):
        """Spins up an in-memory S3 environment"""
        with mock_aws():
            client = boto3.client("s3", region_name="us-east-1")
            client.create_bucket(Bucket="test-data-lake-bucket")
            yield client

    @pytest.fixture
    def subject(self, s3_client) -> S3Service:
        """Provides an S3Service initialized with a moto backend"""
        return S3Service(s3_client=s3_client, bucket_name="test-data-lake-bucket")

    def test_write_json_file_happy_path(self, subject: S3Service, s3_client):
        """Verify JSON payloads are correctly serialized and written to S3."""
        payload = {"station_id": "1", "status": "active"}
        s3_key = "bronze/test_file.json"

        subject.write_json_file(payload, s3_key)

        # Retrieve the object from the moto backend to verify it was written
        response = s3_client.get_object(Bucket=subject.bucket_name, Key=s3_key)
        saved_body = json.loads(response["Body"].read().decode("utf-8"))
        
        assert saved_body == payload
        assert response["ContentType"] == "application/json"

    def test_write_json_file_client_error_raises(self, mocker: MockerFixture, subject: S3Service):
        """Verify ClientErrors during JSON upload are raised."""
        error_response = {"Error": {"Code": "AccessDenied", "Message": "Access Denied"}}
        mocker.patch.object(subject.s3_client, "put_object", side_effect=ClientError(error_response, "PutObject"))

        with pytest.raises(ClientError):
            subject.write_json_file({"data": "test"}, "bronze/test_file.json")

    def test_write_csv_file_object_happy_path(self, subject: S3Service, s3_client):
        """Verify binary file objects (CSVs) are correctly uploaded to S3."""
        csv_content = b"col1,col2\n1,2"
        csv_file = io.BytesIO(csv_content)
        s3_key = "bronze/test_data.csv"

        subject.write_csv_file_object(csv_file, s3_key)

        response = s3_client.get_object(Bucket=subject.bucket_name, Key=s3_key)
        saved_body = response["Body"].read()
        
        assert saved_body == csv_content

    def test_write_csv_file_object_error_raises(self, mocker: MockerFixture, subject: S3Service):
        """Verify generic exceptions during file object upload are raised."""
        mocker.patch.object(subject.s3_client, "upload_fileobj", side_effect=Exception("Connection interrupted"))
        csv_file = io.BytesIO(b"data")

        with pytest.raises(Exception, match="Connection interrupted"):
            subject.write_csv_file_object(csv_file, "bronze/test_data.csv")

    def test_write_success_file_happy_path(self, subject: S3Service, s3_client):
        """Verify the _SUCCESS marker file is written as an empty file with the correct prefix and content type."""
        prefix = "bronze/trips/year=2026"
        expected_key = f"{prefix}/_SUCCESS"

        subject.write_success_file(prefix)

        response = s3_client.get_object(Bucket=subject.bucket_name, Key=expected_key)
        saved_body = response["Body"].read()

        assert saved_body == b""
        assert response["ContentType"] == "application/x-empty"

    def test_write_success_file_client_error_raises(self, mocker: MockerFixture, subject: S3Service):
        """Verify ClientErrors during _SUCCESS file upload are raised."""
        error_response = {"Error": {"Code": "InternalError", "Message": "Internal Error"}}
        mocker.patch.object(subject.s3_client, "put_object", side_effect=ClientError(error_response, "PutObject"))

        with pytest.raises(ClientError):
            subject.write_success_file("bronze/trips")