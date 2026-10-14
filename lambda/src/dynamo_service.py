import logging
from decimal import Decimal, InvalidOperation
from typing import Any

from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class DynamoDBService:
    def __init__(self, dynamodb_client: Any, table_name: str):
        self.table = dynamodb_client.Table(table_name)

    def update_station_status(self, stations: list[dict[str, Any]], updated_at_ts: int) -> int:
        logger.info(f"Updating DynamoDB table with station status for {len(stations)} stations")
        error_count = 0
        for station in stations:
            station_id = str(station.get("station_id"))
            if not station_id:
                logger.info("Skipping station with null station_id")
                error_count += 1
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
                        # GBFS num_bikes_available = ebikes + classic bikes. Our DB should use classic bikes as num_bikes_available.
                        ":bikes": station.get("num_bikes_available") - station.get("num_ebikes_available"),
                        ":ebikes": station.get("num_ebikes_available"),
                        ":docks": station.get("num_docks_available"),
                        ":installed": bool(station.get("is_installed")),
                        ":renting": bool(station.get("is_renting")),
                        ":returning": bool(station.get("is_returning")),
                        ":updated_at": updated_at_ts
                    }
                )
            except ClientError as e:
                logger.error(f"Error updating status for station {station_id}: {e.response['Error']['Message']}")
                error_count += 1
            except Exception:
                logger.exception(f"Unexpected exception updating status for station {station_id}")
                error_count += 1

        logger.info(f"Successfully updated status for {len(stations)-error_count} stations in DynamoDB. Error count: {error_count}")
        return error_count

    def update_station_info(self, stations: list[dict[str, Any]], updated_at_ts: int) -> int:
        logger.info(f"Updating DynamoDB table with station info for {len(stations)} stations")
        error_count = 0
        for station in stations:
            station_id = str(station.get("station_id"))
            if not station_id:
                logger.info("Skipping station with null station_id")
                error_count += 1
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
                        ":station_name": station.get("name"),
                        ":short_name": station.get("short_name"),
                        ":lat": self._to_float(station.get("lat")),
                        ":lon": self._to_float(station.get("lon")),
                        ":capacity": station.get("capacity"),
                        ":updated_at": updated_at_ts
                    }
                )
            except ClientError as e:
                logger.error(f"Error updating info for station {station_id}: {e.response['Error']['Message']}")
                error_count += 1
            except Exception:
                logger.exception(f"Unexpected exception updating info for station {station_id}")
                error_count += 1

        logger.info(f"Successfully updated info for {len(stations)-error_count}/{len(stations)} stations in DynamoDB. Error count: {error_count}")
        return error_count

    def _to_float(self, val):
        try:
            return Decimal(str(val)) if val is not None else None
        except (ValueError, TypeError, InvalidOperation):
            return None


