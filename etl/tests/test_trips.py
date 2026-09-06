from chispa.dataframe_comparer import assert_df_equality
from src.citibike_etl.transformations.trips import transform_trips_bronze_to_silver

def test_transform_trips_filters_invalid_durations(spark):
    input_data = [
        # Valid: 5 minutes
        ("1", "classic_bike", "2026-08-01 10:00:00", "2026-08-01 10:05:00", "Station A", "A", "Station B", "B", "40.0", "-73.0", "40.1", "-73.1", "member"),
        # Invalid: < 60 seconds
        ("2", "electric_bike", "2026-08-01 10:00:00", "2026-08-01 10:00:30", "Station A", "A", "Station B", "B", "40.0", "-73.0", "40.1", "-73.1", "member"),
        # Invalid: > 1 day
        ("2", "classic_bike", "2026-08-01 10:00:00", "2026-08-03 10:00:30", "Station A", "A", "Station B", "B", "40.0", "-73.0", "40.1", "-73.1", "casual"),
    ]
    
    columns = [
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
    input_df = spark.createDataFrame(input_data, columns)
    
    actual_df = transform_trips_bronze_to_silver(input_df).select("ride_id", "duration_seconds")
    actual_df.show()
    
    expected_data = [
        ("1", 300)
    ]
    expected_df = spark.createDataFrame(expected_data, ["ride_id", "duration_seconds"])
    
    assert_df_equality(actual_df, expected_df)