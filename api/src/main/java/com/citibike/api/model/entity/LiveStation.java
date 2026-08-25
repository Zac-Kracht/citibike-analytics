package com.citibike.api.model.entity;

import lombok.NoArgsConstructor;
import lombok.Setter;
import software.amazon.awssdk.enhanced.dynamodb.mapper.annotations.DynamoDbBean;
import software.amazon.awssdk.enhanced.dynamodb.mapper.annotations.DynamoDbPartitionKey;
import software.amazon.awssdk.enhanced.dynamodb.mapper.annotations.DynamoDbAttribute;

@Setter
@NoArgsConstructor
@DynamoDbBean
public class LiveStation {

    private String stationId;
    private String stationName;
    private String shortName;
    private Integer bikesAvailable;
    private Integer ebikesAvailable;
    private Integer docksAvailable;
    private Boolean installed;
    private Boolean renting;
    private Boolean returning;
    private Double latitude;
    private Double longitude;
    private Integer capacity;
    private Integer infoLastUpdated;
    private Integer statusLastUpdated;

    @DynamoDbPartitionKey
    @DynamoDbAttribute("station_id")
    public String getStationId() {
        return stationId;
    }

    @DynamoDbAttribute("station_name")
    public String getStationName() {
        return stationName;
    }

    @DynamoDbAttribute("short_name")
    public String getShortName() {
        return shortName;
    }

    @DynamoDbAttribute("num_bikes_available")
    public Integer getBikesAvailable() {
        return bikesAvailable;
    }

    @DynamoDbAttribute("num_ebikes_available")
    public Integer getEbikesAvailable() {
        return ebikesAvailable;
    }

    @DynamoDbAttribute("num_docks_available")
    public Integer getDocksAvailable() {
        return docksAvailable;
    }

    @DynamoDbAttribute("is_installed")
    public Boolean getInstalled() {
        return installed;
    }

    @DynamoDbAttribute("is_renting")
    public Boolean getRenting() {
        return renting;
    }

    @DynamoDbAttribute("is_returning")
    public Boolean getReturning() {
        return returning;
    }

    @DynamoDbAttribute("latitude")
    public Double getLatitude() {
        return latitude;
    }

    @DynamoDbAttribute("longitude")
    public Double getLongitude() {
        return longitude;
    }

    @DynamoDbAttribute("capacity")
    public Integer getCapacity() {
        return capacity;
    }

    @DynamoDbAttribute("info_last_updated")
    public Integer getInfoLastUpdated() {
        return infoLastUpdated;
    }

    @DynamoDbAttribute("status_last_updated")
    public Integer getStatusLastUpdated() {
        return statusLastUpdated;
    }

}
