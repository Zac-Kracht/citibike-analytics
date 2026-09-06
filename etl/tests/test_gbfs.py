from chispa.dataframe_comparer import assert_df_equality
from datetime import datetime
from pyspark.sql.types import StructType, StructField, StringType, TimestampType, IntegerType, DoubleType

from src.citibike_etl.transformations.gbfs import (
    transform_gbfs_station_info_bronze_to_silver,
    transform_gbfs_station_status_bronze_to_silver
)

def test_transform_gbfs_station_status_bronze_to_silver(spark):
    input_data = [
        ({
            "data": {
                "stations": [
                    # Valid
                    {
                        "station_id": "id123",
                        "num_bikes_available": 12,
                        "num_docks_available": 9,
                        "num_ebikes_available": 5,
                        "is_installed": 1,
                        "is_renting": 1,
                        "is_returning": 1,
                    },
                    # Invalid, null station_id
                    {
                        "station_id": None,
                        "num_bikes_available": 12,
                        "num_docks_available": 9,
                        "num_ebikes_available": 12,
                        "is_installed": 1,
                        "is_renting": 1,
                        "is_returning": 1,
                    },
                    # Invalid, is_installed=0
                    {
                        "station_id": "id123",
                        "num_bikes_available": 12,
                        "num_docks_available": 9,
                        "num_ebikes_available": 12,
                        "is_installed": 0,
                        "is_renting": 1,
                        "is_returning": 1,
                    },
                    # Invalid, incorrect number of bikes/ebikes
                    {
                        "station_id": "id123",
                        "num_bikes_available": 10,
                        "num_docks_available": 5,
                        "num_ebikes_available": 15,
                        "is_installed": 1,
                        "is_renting": 1,
                        "is_returning": 1,
                    },
                ]
            },
            "last_updated": 1788728090
        })
    ]
    
    input_columns = [
        "data",
        "last_updated"
    ]
    input_df = spark.createDataFrame(input_data, input_columns)
    
    actual_df = transform_gbfs_station_status_bronze_to_silver(input_df)
    
    expected_data = [
        ("id123", 9, 5, datetime(2026,9,6,16,54,50), 7, 2026, 9),
    ]
    final_schema = StructType([
        StructField("station_id", StringType(), True),
        StructField("num_docks_available", IntegerType(), True),
        StructField("num_ebikes_available", IntegerType(), True),
        StructField("snapshot_timestamp", TimestampType(), True),
        StructField("num_classic_bikes_available", IntegerType(), True),
        StructField("year", IntegerType(), True),
        StructField("month", IntegerType(), True),
    ])
    expected_df = spark.createDataFrame(expected_data, final_schema)
    
    assert_df_equality(actual_df, expected_df)

def test_transform_gbfs_station_info_bronze_to_silver(spark):
    input_data = [
        ({
            "data": {
                "stations": [
                    # Valid
                    {
                        "station_id": "id123",
                        "name": "1 St",
                        "short_name": "100.01",
                        "lon": "-74.01",
                        "lat": "40.65",
                        "region_id": "71",
                        "capacity": "40"
                    },
                    # Invalid, null station_id
                    {
                        "station_id": None,
                        "name": "1 St",
                        "short_name": "100.01",
                        "lon": "-74.01",
                        "lat": "40.65",
                        "region_id": "71",
                        "capacity": "40"
                    },
                    # Invalid, null short_name
                    {
                        "station_id": "id123",
                        "name": "1 St",
                        "short_name": None,
                        "lon": "-74.01",
                        "lat": "40.65",
                        "region_id": "71",
                        "capacity": "40"
                    }
                ]
            },
            "last_updated": 1788728090
        })
    ]
    
    input_columns = [
        "data",
        "last_updated"
    ]
    input_df = spark.createDataFrame(input_data, input_columns)
    
    actual_df = transform_gbfs_station_info_bronze_to_silver(input_df)
    
    expected_data = [
        ("id123", "100.01", "1 St", "71", 40.65, -74.01, 40, datetime(2026,9,6,16,54,50), 2026, 9)
    ]
    final_schema = StructType([
        StructField("station_id", StringType(), True),
        StructField("short_name", StringType(), True),
        StructField("station_name", StringType(), True),
        StructField("region_id", StringType(), True),
        StructField("lat", DoubleType(), True),
        StructField("lon", DoubleType(), True),
        StructField("capacity", IntegerType(), True),
        StructField("snapshot_timestamp", TimestampType(), True),
        StructField("year", IntegerType(), True),
        StructField("month", IntegerType(), True),
    ])
    expected_df = spark.createDataFrame(expected_data, final_schema)
    
    assert_df_equality(actual_df, expected_df)
    