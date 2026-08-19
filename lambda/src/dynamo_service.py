import logging

from typing import Any, Dict
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class DynamoDBService():
    def __init__(self, dynamodb_client: Any, table_name: str):
        self.table = dynamodb_client.Table(table_name)

    def update_station_status(self, stations: list[Dict[str, Any]], updated_at_ts: int) -> int:
        logger.info(f"Updating DynamoDB table with station status for {len(stations)} stations")
        error_count = 0
        for station in stations:
            station_id = str(station.get("station_id"))
            if not station_id:
                continue

            try:
                self.table.update_item(
                    Key={"station_id": station_id},
                    UpdateExpression="""
                        SET num_bikes_available = :bikes,
                            num_ebikes_available = :ebikes,
                            num_docks_available = :docks,
                            is_installed = :installed,
                            is_renting = :renting,
                            is_returning = :returning,
                            status_last_updated = :updated_at
                    """,
                    ExpressionAttributeValues={
                        ":bikes": station.get("num_bikes_available", 0),
                        ":ebikes": station.get("num_ebikes_available", 0),
                        ":docks": station.get("num_docks_available", 0),
                        ":installed": bool(station.get("is_installed", 1)),
                        ":renting": bool(station.get("is_renting", 1)),
                        ":returning": bool(station.get("is_returning", 1)),
                        ":updated_at": updated_at_ts
                    }
                )
            except ClientError as e:
                logger.error(f"Error updating status for station {station_id}: {e.response['Error']['Message']}")
                error_count += 1
            except Exception as e:
                logger.error(f"Unexpected exception updating status for station {station_id}: {str(e)}", exc_info=True)
                error_count += 1

        logger.info(f"Successfully updated status for {len(stations)-error_count} stations in DynamoDB. Error count: {error_count}")
        return error_count

    def update_station_info(self, stations: list[Dict[str, Any]], updated_at_ts: int) -> int:
        logger.info(f"Updating DynamoDB table with station info for {len(stations)} stations")
        error_count = 0
        for station in stations:
            station_id = str(station.get("station_id"))
            if not station_id:
                continue

            try:
                self.table.update_item(
                    Key={"station_id": station_id},
                    UpdateExpression="""
                        SET station_name = :station_name,
                            short_name = :short_name,
                            latitude = :lat,
                            longitude = :lon,
                            #capacity = :capacity,
                            info_last_updated = :updated_at
                    """,
                    ExpressionAttributeNames={
                        "#capacity": "capacity"  # 'capacity' is a reserved keyword in DynamoDB
                    },
                    ExpressionAttributeValues={
                        ":station_name": station.get("name", ""),
                        ":short_name": station.get("short_name", ""),
                        ":lat": self._to_float(station.get("lat")),
                        ":lon": self._to_float(station.get("lon")),
                        ":capacity": station.get("capacity", 0),
                        ":updated_at": updated_at_ts
                    }
                )
            except ClientError as e:
                logger.error(f"Error updating info for station {station_id}: {e.response['Error']['Message']}")
                error_count += 1
            except Exception as e:
                logger.error(f"Unexpected exception updating info for station {station_id}: {str(e)}", exc_info=True)
                error_count += 1

        logger.info(f"Successfully updated info for {len(stations)-error_count}/{len(stations)} stations in DynamoDB. Error count: {error_count}")
        return error_count

    def _to_float(val):
        try:
            return float(val) if val is not None else None
        except (ValueError, TypeError):
            return None


