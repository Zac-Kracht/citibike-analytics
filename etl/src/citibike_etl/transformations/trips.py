from pyspark.sql import DataFrame
from pyspark.sql.functions import col, month, to_timestamp, unix_timestamp, year
from pyspark.sql.types import DoubleType

from utils.logging import get_logger

logger = get_logger(__name__)

def transform_trips_bronze_to_silver(trips_df: DataFrame) -> DataFrame:
    """"""
    # Remove nulls from non-nullable fields
    trips_df = trips_df.dropna(
        subset=[
            "ride_id", 
            "started_at", 
            "ended_at", 
            "start_station_id", 
            "end_station_id", 
            "start_lat", 
            "start_lng", 
            "end_lat", 
            "end_lng"
        ]
    )

    # Convert to correct datatypes
    trips_df = (
        trips_df.withColumn("started_at", to_timestamp("started_at"))
        .withColumn("ended_at", to_timestamp("ended_at"))
        .withColumn("start_lat", col("start_lat").cast(DoubleType()))
        .withColumn("start_lng", col("start_lng").cast(DoubleType()))
        .withColumn("end_lat", col("end_lat").cast(DoubleType()))
        .withColumn("end_lng", col("end_lng").cast(DoubleType()))
        .withColumn("duration_seconds", unix_timestamp("ended_at") - unix_timestamp("started_at"))
    )

    # Filter invalid trip durations
    trips_df = trips_df.filter(
        (col("duration_seconds") >= 60)
        & (col("duration_seconds") <= 86400)
    )

    # Partition cols
    trips_df = (
        trips_df.withColumn("year", year("started_at"))
        .withColumn("month", month("started_at"))
    )

    # Final columns
    return trips_df.select(
        "ride_id",
        "rideable_type",
        "started_at",
        "ended_at",
        "start_station_name",
        "start_station_id",
        "end_station_name",
        "end_station_id",
        "start_lat", 
        "start_lng", 
        "end_lat", 
        "end_lng",
        "member_casual",
        "duration_seconds",
        "year",
        "month"
    )