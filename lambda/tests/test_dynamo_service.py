import os
from decimal import Decimal

import boto3
import pytest
from botocore.exceptions import ClientError
from moto import mock_aws
from pytest_mock import MockerFixture

from src.dynamo_service import DynamoDBService


class TestDynamoDBService:

    @pytest.fixture
    def aws_credentials(self):
        """Mocked AWS Credentials for moto"""
        os.environ["AWS_ACCESS_KEY_ID"] = "testing"
        os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
        os.environ["AWS_SECURITY_TOKEN"] = "testing"
        os.environ["AWS_SESSION_TOKEN"] = "testing"
        os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

    @pytest.fixture
    def dynamodb_resource(self, aws_credentials):
        """Spins up an in-memory DynamoDB environment"""
        with mock_aws():
            yield boto3.resource("dynamodb", region_name="us-east-1")

    @pytest.fixture
    def test_table(self, dynamodb_resource):
        """Creates a realistic DynamoDB table for testing"""
        table_name = "test_station_data"
        table = dynamodb_resource.create_table(
            TableName=table_name,
            KeySchema=[{"AttributeName": "station_id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "station_id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST"
        )
        table.meta.client.get_waiter("table_exists").wait(TableName=table_name)
        return table_name

    @pytest.fixture
    def subject(self, dynamodb_resource, test_table) -> DynamoDBService:
        """Provides a DynamoDBService initialized with a moto backend"""
        return DynamoDBService(dynamodb_client=dynamodb_resource, table_name=test_table)

    def test_to_float_valid_number(self, subject: DynamoDBService):
        """Test float/int conversion returns Decimal"""
        result = subject._to_float(45.5)
        assert isinstance(result, Decimal)
        assert result == Decimal("45.5")

    def test_to_float_none(self, subject: DynamoDBService):
        """Test _to_float handles None appropriately"""
        assert subject._to_float(None) is None

    def test_to_float_invalid_value(self, subject: DynamoDBService):
        """Test _to_float handles invalid types safely"""
        assert subject._to_float("invalid_string") is None

    def test_update_station_status_happy_path(self, subject: DynamoDBService, dynamodb_resource, test_table):
        """Test status update successfully writes the expected data to DynamoDB"""
        stations = [
            {
                "station_id": "1",
                "num_bikes_available": 10,
                "num_ebikes_available": 2,
                "num_docks_available": 5,
                "is_installed": 1,
                "is_renting": 1,
                "is_returning": 1
            }
        ]
        errors = subject.update_station_status(stations, updated_at_ts=1234567890)
        
        assert errors == 0
        
        # Verify the data was actually written correctly
        table = dynamodb_resource.Table(test_table)
        response = table.get_item(Key={"station_id": "1"})
        item = response.get("Item", {})
        
        assert item["num_bikes_available"] == Decimal(8)
        assert item["num_ebikes_available"] == Decimal(2)
        assert item["is_installed"] is True
        assert item["status_last_updated"] == Decimal(1234567890)
        
    def test_update_station_status_missing_id(self, subject: DynamoDBService):
        """Test status update skips items missing a station_id"""
        stations = [{"num_bikes_available": 10}]
        
        errors = subject.update_station_status(stations, updated_at_ts=1234567890)
        
        assert errors == 1

    def test_update_station_status_client_error(self, mocker: MockerFixture, subject: DynamoDBService):
        """Test status update catches ClientError and increments error count"""
        stations = [{"station_id": "1"}]
        error_response = {"Error": {"Message": "Provisioned throughput exceeded", "Code": "ProvisionedThroughputExceededException"}}
        
        mocker.patch.object(subject.table, "update_item", side_effect=ClientError(error_response, "UpdateItem"))
        
        errors = subject.update_station_status(stations, updated_at_ts=1234567890)
        
        assert errors == 1

    def test_update_station_status_generic_exception(self, mocker: MockerFixture, subject: DynamoDBService):
        """Test status update catches generic exceptions and increments error count"""
        stations = [{"station_id": "1"}]
        mocker.patch.object(subject.table, "update_item", side_effect=Exception("Unexpected connection failure"))
        
        errors = subject.update_station_status(stations, updated_at_ts=1234567890)
        
        assert errors == 1

    def test_update_station_info_happy_path(self, subject: DynamoDBService, dynamodb_resource, test_table):
        """Test info update successfully handles reserved keywords and correctly formats DB items"""
        stations = [
            {
                "station_id": "1",
                "name": "Main St & 1st Ave",
                "short_name": "MS1",
                "lat": 40.7128,
                "lon": -74.0060,
                "capacity": 20
            }
        ]
        errors = subject.update_station_info(stations, updated_at_ts=1234567890)
        
        assert errors == 0
        
        table = dynamodb_resource.Table(test_table)
        response = table.get_item(Key={"station_id": "1"})
        item = response.get("Item", {})
        
        assert item["station_name"] == "Main St & 1st Ave"
        assert item["latitude"] == Decimal("40.7128")
        assert item["capacity"] == Decimal(20)
        assert item["info_last_updated"] == Decimal(1234567890)

    def test_update_station_info_client_error(self, mocker: MockerFixture, subject: DynamoDBService):
        """Test info update catches ClientError and increments error count"""
        stations = [{"station_id": "1"}]
        error_response = {"Error": {"Message": "ValidationException", "Code": "ValidationException"}}
        
        mocker.patch.object(subject.table, "update_item", side_effect=ClientError(error_response, "UpdateItem"))
        
        errors = subject.update_station_info(stations, updated_at_ts=1234567890)
        
        assert errors == 1
        