from chispa.dataframe_comparer import assert_df_equality
from datetime import datetime
from pyspark.sql.types import StructType, StructField, StringType, LongType, TimestampType, DoubleType, IntegerType

from src.citibike_etl.transformations.trips import transform_trips_bronze_to_silver

def test_transform_trips_filters_invalid_durations(spark):
    input_data = [
        # Valid: 5 minutes
        ("1", "classic_bike", "2026-08-01 10:00:00", "2026-08-01 10:05:00", "Station A", "A", "Station B", "B", "40.0", "-73.0", "40.1", "-73.1", "member"),
        # Invalid: < 60 seconds
        ("2", "electric_bike", "2026-08-01 10:00:00", "2026-08-01 10:00:30", "Station A", "A", "Station B", "B", "40.0", "-73.0", "40.1", "-73.1", "member"),
        # Invalid: > 1 day
        ("2", "classic_bike", "2026-08-01 10:00:00", "2026-08-03 10:00:30", "Station A", "A", "Station B", "B", "40.0", "-73.0", "40.1", "-73.1", "casual"),
        # Invlid: null ride_id
        (None, "classic_bike", "2026-08-01 10:00:00", "2026-08-01 10:05:00", "Station A", "A", "Station B", "B", "40.0", "-73.0", "40.1", "-73.1", "member"),
    ]
    
    input_columns = [
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
        "member_casual"
    ]
    input_df = spark.createDataFrame(input_data, input_columns)
    
    actual_df = transform_trips_bronze_to_silver(input_df)
    
    expected_data = [
        ("1", "classic_bike", datetime(2026,8,1,10,0,0), datetime(2026,8,1,10,5,0), "Station A", "A", "Station B", "B", 40.0, -73.0, 40.1, -73.1, "member", 300, 2026, 8),
    ]
    final_schema = StructType([
        StructField("ride_id", StringType(), True),
        StructField("rideable_type", StringType(), True),
        StructField("started_at", TimestampType(), True),
        StructField("ended_at", TimestampType(), True),
        StructField("start_station_name", StringType(), True),
        StructField("start_station_id", StringType(), True),
        StructField("end_station_name", StringType(), True),
        StructField("end_station_id", StringType(), True),
        StructField('start_lat', DoubleType(), True),
        StructField('start_lng', DoubleType(), True),
        StructField('end_lat', DoubleType(), True),
        StructField('end_lng', DoubleType(), True),
        StructField("member_casual", StringType(), True),
        StructField("duration_seconds", LongType(), True),
        StructField("year", IntegerType(), True),
        StructField("month", IntegerType(), True)
    ])
    expected_df = spark.createDataFrame(expected_data, final_schema)
    
    assert_df_equality(actual_df, expected_df)
    