import pytest
import json
import urllib.error
from pytest_mock import MockerFixture
from src.gbfs_client import GBFSClient

class TestGBFSClient:

    @pytest.fixture
    def subject(self):
        return GBFSClient(
            discovery_url="http://mock-url.com/gbfs.json",
            user_agent="Test/1.0"
        )

    @pytest.fixture
    def mock_discovery_data(self):
        return {
            "data": {
                "en": {
                    "feeds": [
                        {"name": "station_information", "url": "http://mock-url.com/station_information.json"},
                        {"name": "station_status", "url": "http://mock-url.com/station_status.json"}
                    ]
                }
            }
        }

    def test_make_gbfs_request_success_response(self, mocker: MockerFixture, subject):
        """Test GBFS data retrieval on 200 response"""
        mock_urlopen = mocker.patch("urllib.request.urlopen")
        mock_response = mocker.MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps({"status": "success"}).encode("utf-8")
        mock_response.__enter__.return_value = mock_response 
        mock_urlopen.return_value = mock_response

        result = subject._make_gbfs_request("http://mock-url.com/test.json")

        assert result == {"status": "success"}
        mock_urlopen.assert_called_once()

    def test_make_gbfs_request_unexpected_http_status(self):
        pass

    def test_make_gbfs_request_http_exception(self):
        pass

    def test_make_gbfs_request_invalid_response(self):
        pass

    def test__get_gbfs_feed_data_not_set(self):
        pass

    def test__get_gbfs_feed_data_set(self):
        pass

    def test__get_gbfs_feed_missing_key(self):
        pass

    def test_fetch_station_info_happy_path(self):
        pass

    def test_fetch_station_status_happy_path(self):
        pass
