from pyspark.sql import DataFrame
from pyspark.sql.functions import explode, col, timestamp_seconds, year, month
from pyspark.sql.types import StringType, DoubleType, IntegerType

from src.citibike_etl.utils.logging import get_logger

logger = get_logger(__name__)

def transform_gbfs_station_status_bronze_to_silver(status_df: DataFrame) -> DataFrame:
    """Transform bronze GBFS station_status JSON data to silver layer"""
    status_df = status_df.select(
        explode("data.stations").alias("station"),
        timestamp_seconds("last_updated").alias("snapshot_timestamp")
    )  

    status_df = status_df.select(
        col("station.station_id").cast(StringType()).alias("station_id"),
        col("station.num_bikes_available").cast(IntegerType()).alias("num_bikes_available"),
        col("station.num_docks_available").cast(IntegerType()).alias("num_docks_available"),
        col("station.num_ebikes_available").cast(IntegerType()).alias("num_ebikes_available"),
        col("station.is_installed").cast(IntegerType()).alias("is_installed"),
        "snapshot_timestamp"
    )

    status_df = status_df.dropna(subset=["station_id", "num_bikes_available", "num_ebikes_available", "is_installed"])
    status_df = status_df.filter(col("is_installed") == 1).drop("is_installed")

    status_df = status_df.withColumn(
        "num_classic_bikes_available", col("num_bikes_available") - col("num_ebikes_available")
    )
    status_df = status_df.filter(col("num_classic_bikes_available") >= 0).drop("num_bikes_available")

    return (
        status_df
        .withColumn("year", year("snapshot_timestamp"))
        .withColumn("month", month("snapshot_timestamp"))
    )


def transform_gbfs_station_info_bronze_to_silver(info_df: DataFrame) -> DataFrame:
    """Transform bronze GBFS station_info JSON data to silver layer"""
    info_df = info_df.select(
        explode("data.stations").alias("station"),
        timestamp_seconds("last_updated").alias("snapshot_timestamp")
    )    

    info_df = info_df.select(
        col("station.station_id").cast(StringType()).alias("station_id"),
        col("station.short_name").cast(StringType()).alias("short_name"),
        col("station.name").cast(StringType()).alias("station_name"),
        col("station.region_id").cast(StringType()).alias("region_id"),
        col("station.lat").cast(DoubleType()).alias("lat"),
        col("station.lon").cast(DoubleType()).alias("lon"),
        col("station.capacity").cast(IntegerType()).alias("capacity"),
        "snapshot_timestamp"
    )

    info_df = info_df.dropna(subset=["station_id", "short_name"])

    return (
        info_df
        .withColumn("year", year("snapshot_timestamp"))
        .withColumn("month", month("snapshot_timestamp"))
    )