package com.citibike.api.model.dto;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
@JsonInclude(JsonInclude.Include.NON_NULL)
public class StationsResponseDTO {
    
    @JsonProperty("stationId")
    private String stationId;

    @JsonProperty("stationName")
    private String stationName;

    @JsonProperty("bikesAvailable")
    private Integer bikesAvailable;

    @JsonProperty("ebikesAvailable")
    private Integer ebikesAvailable;

    @JsonProperty("docksAvailable")
    private Integer docksAvailable;

    @JsonProperty("isInstalled")
    private Boolean installed;

    @JsonProperty("isRenting")
    private Boolean renting;

    @JsonProperty("isReturning")
    private Boolean returning;

    @JsonProperty("latitude")
    private Double latitude;

    @JsonProperty("longitude")
    private Double longitude;

    @JsonProperty("capacity")
    private Integer capacity;

}
