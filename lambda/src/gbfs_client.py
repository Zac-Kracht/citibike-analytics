import json
import urllib.request
import logging

from typing import Final, Dict, Any

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class GBFSClient:
    GBFS_KEY_STATION_STATUS: Final = "station_status"
    GBFS_KEY_STATION_INFORMATION: Final = "station_information"

    def __init__(self, discovery_url: str, language_code: str = "en", owner_contact: str = "", env: str = "dev"):
        self.discovery_url = discovery_url
        self.language_code = language_code
        self.owner_contact = owner_contact
        self.env = env
        self.feed_data = None

    def _make_gbfs_request(self, url: str):
        logging.info(f"Making request to url: {url}")
        req = urllib.request.Request(
            url,
            headers = {
                "User-Agent": f"CitiBikeAnalytics-Ingestion-Lambda-{self.env}/1.0 ({self.owner_contact})"
            }
        )

        try: 
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    return json.loads(response.read().decode("utf-8"))
                else:
                    logger.error(f"Unexpected HTTP status from url {url}: {response.status}")
                    raise RuntimeError(f"Response from {url} returned unexpected status: {response.status}")
        except urllib.error.HTTPError as e:
            logger.error(f"HTTP Error from url {url} {e.code}: {e.reason}")
            raise e
        except urllib.error.URLError as e:
            logger.error(f"URL Error: {e.reason}")
            raise e
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from url {url}: {e}")
            raise e

    def _get_gbfs_feed(self, key: str):
        if not self.feed_data:
            logging.info("Initializing GBFS feed data...")
            discovery_json = self._make_gbfs_request(self.discovery_url)
            discovery_languages = discovery_json.get("data", {})
            discovery_feeds = discovery_languages.get(self.language_code, {}).get("feeds", [])

            self.feed_data = {}
            for feed in discovery_feeds:
                self.feed_data[feed["name"]] = feed["url"]
            logging.info("GBFS feed data initialized")

        if key in self.feed_data:
            return self.feed_data[key]
        else:
            logger.error(f"Key {key} not found in GBFS feed data. Available keys: {list(self.feed_data.keys())}")
            raise RuntimeError(f"Key {key} not found in GBFS feed data")


    def fetch_station_info(self) -> Dict[str, Any]:
        url = self._get_gbfs_feed(self.GBFS_KEY_STATION_INFORMATION)
        return self._make_gbfs_request(url)

    def fetch_station_status(self) -> Dict[str, Any]:
        url = self._get_gbfs_feed(self.GBFS_KEY_STATION_STATUS)
        return self._make_gbfs_request(url)
