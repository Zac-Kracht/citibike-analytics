package com.citibike.api.model.entity;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import software.amazon.awssdk.enhanced.dynamodb.mapper.annotations.DynamoDbBean;
import software.amazon.awssdk.enhanced.dynamodb.mapper.annotations.DynamoDbPartitionKey;
import software.amazon.awssdk.enhanced.dynamodb.mapper.annotations.DynamoDbAttribute;

@Getter
@Setter
@NoArgsConstructor
@DynamoDbBean
public class LiveStation {

    @Getter(onMethod_ = {@DynamoDbPartitionKey, @DynamoDbAttribute("user_id")})
    private String stationId;

    @Getter(onMethod_ = {@DynamoDbAttribute("station_name")})
    private String stationName;

    @Getter(onMethod_ = {@DynamoDbAttribute("short_name")})
    private String shortName;

    @Getter(onMethod_ = {@DynamoDbAttribute("num_bikes_available")})
    private Integer bikesAvailable;

    @Getter(onMethod_ = {@DynamoDbAttribute("num_ebikes_available")})
    private Integer ebikesAvailable;

    @Getter(onMethod_ = {@DynamoDbAttribute("num_docks_available")})
    private Integer docksAvailable;

    @Getter(onMethod_ = {@DynamoDbAttribute("is_installed")})
    private Boolean installed;

    @Getter(onMethod_ = {@DynamoDbAttribute("is_renting")})
    private Boolean renting;

    @Getter(onMethod_ = {@DynamoDbAttribute("is_returning")})
    private Boolean returning;

    @Getter(onMethod_ = {@DynamoDbAttribute("latitude")})
    private Double latitude;

    @Getter(onMethod_ = {@DynamoDbAttribute("longitude")})
    private Double longitude;

    @Getter(onMethod_ = {@DynamoDbAttribute("capacity")})
    private Integer capacity;

    @Getter(onMethod_ = {@DynamoDbAttribute("info_last_updated")})
    private Integer infoLastUpdated;

    @Getter(onMethod_ = {@DynamoDbAttribute("status_last_updated")})
    private Integer statusLastUpdated;

}
