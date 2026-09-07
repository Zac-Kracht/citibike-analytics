import json
from urllib.error import HTTPError

import pytest
from pytest_mock import MockerFixture

from src.gbfs_client import GBFSClient


class TestGBFSClient:

    @pytest.fixture
    def subject(self) -> GBFSClient:
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

    def test_make_gbfs_request_happy_path(self, mocker: MockerFixture, subject: GBFSClient):
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

    def test_make_gbfs_request_unexpected_http_status(self, mocker: MockerFixture, subject: GBFSClient):
        """Test GBFS data retrieval throws RuntimeError on 4xx response"""
        mock_urlopen = mocker.patch("urllib.request.urlopen")
        mock_response = mocker.MagicMock()
        mock_response.status = 404
        mock_response.__enter__.return_value = mock_response 
        mock_urlopen.return_value = mock_response

        with pytest.raises(RuntimeError, match="returned unexpected status"):
            subject._make_gbfs_request("http://mock-url.com/test.json")

        mock_urlopen.assert_called_once()

    def test_make_gbfs_request_http_exception(self, mocker: MockerFixture, subject: GBFSClient):
        """Test GBFS request persists HTTPError"""
        mock_urlopen = mocker.patch("urllib.request.urlopen")
        mock_urlopen.side_effect = HTTPError(
            url="http://mock-url.com",
            code=404,
            msg="Not Found",
            hdrs=None,
            fp=None
        )

        with pytest.raises(HTTPError):
            subject._make_gbfs_request("http://mock-url.com/test.json")
        
        mock_urlopen.assert_called_once()

    def test_make_gbfs_request_invalid_response(self, mocker: MockerFixture, subject: GBFSClient):
        """Test JSONDecodeError is raised when response is invalid JSON"""
        mock_urlopen = mocker.patch("urllib.request.urlopen")
        mock_response = mocker.MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = b"{invalid_json:"
        mock_response.__enter__.return_value = mock_response 
        mock_urlopen.return_value = mock_response

        with pytest.raises(json.JSONDecodeError):
            subject._make_gbfs_request("http://mock-url.com/test.json")
            
        mock_urlopen.assert_called_once()

    def test_get_gbfs_feed_data_not_set(self, mocker: MockerFixture, subject: GBFSClient, mock_discovery_data: dict):
        """Test feed data initialization when feed_data is None"""
        mock_make_request = mocker.patch.object(subject, "_make_gbfs_request")
        mock_make_request.return_value = mock_discovery_data
        
        url = subject._get_gbfs_feed("station_status")
        
        assert url == "http://mock-url.com/station_status.json"
        assert subject.feed_data == {
            "station_information": "http://mock-url.com/station_information.json",
            "station_status": "http://mock-url.com/station_status.json"
        }
        mock_make_request.assert_called_once_with("http://mock-url.com/gbfs.json")

    def test_get_gbfs_feed_data_set(self, mocker: MockerFixture, subject: GBFSClient):
        """Test retrieving a feed URL from cached feed_data"""
        mock_make_request = mocker.patch.object(subject, "_make_gbfs_request")
        subject.feed_data = {"station_status": "http://cached-url.com/station_status.json"}
        
        url = subject._get_gbfs_feed("station_status")
        
        assert url == "http://cached-url.com/station_status.json"
        mock_make_request.assert_not_called()

    def test_get_gbfs_feed_missing_key(self, subject: GBFSClient):
        """Test RuntimeError is raised when the requested key is missing"""
        subject.feed_data = {"station_status": "http://mock-url.com/station_status.json"}
        
        with pytest.raises(RuntimeError, match="Key invalid_key not found in GBFS feed data"):
            subject._get_gbfs_feed("invalid_key")

    def test_fetch_station_info_happy_path(self, mocker: MockerFixture, subject: GBFSClient):
        """Test fetch_station_info delegates properly"""
        mock_get_feed = mocker.patch.object(subject, "_get_gbfs_feed", return_value="http://mock-url.com/info.json")
        mock_make_request = mocker.patch.object(subject, "_make_gbfs_request", return_value={"data": {"stations": []}})
        
        result = subject.fetch_station_info()
        
        assert result == {"data": {"stations": []}}
        mock_get_feed.assert_called_once_with(GBFSClient.GBFS_KEY_STATION_INFORMATION)
        mock_make_request.assert_called_once_with("http://mock-url.com/info.json")

    def test_fetch_station_status_happy_path(self, mocker: MockerFixture, subject: GBFSClient):
        """Test fetch_station_status delegates properly"""
        mock_get_feed = mocker.patch.object(subject, "_get_gbfs_feed", return_value="http://mock-url.com/status.json")
        mock_make_request = mocker.patch.object(subject, "_make_gbfs_request", return_value={"data": {"stations": []}})
        
        result = subject.fetch_station_status()
        
        assert result == {"data": {"stations": []}}
        mock_get_feed.assert_called_once_with(GBFSClient.GBFS_KEY_STATION_STATUS)
        mock_make_request.assert_called_once_with("http://mock-url.com/status.json")
