package com.citibike.api.mapper;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;

import java.util.Collections;
import java.util.List;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.mapstruct.factory.Mappers;

import com.citibike.api.model.dto.StationsResponseDTO;
import com.citibike.api.model.entity.LiveStation;

public class StationMapperTest {

    private final StationMapper subject = Mappers.getMapper(StationMapper.class);

    @Test
    @DisplayName("toResponseDTO mapping should return StationsResponseDTO with valid mappings")
    void toResponseDTO_CorrectMapping_ReturnsDTOObject() {
        LiveStation testStation = createTestLiveStation("test_station");

        StationsResponseDTO result = subject.toResponseDTO(testStation);

        assertNotNull(result);
        assertEquals(testStation.getStationId(), result.getStationId());
        assertEquals(testStation.getStationName(), result.getStationName());
        assertNull(result.getReturning());
        assertEquals(testStation.getBikesAvailable(), result.getBikesAvailable());
        assertEquals(testStation.getEbikesAvailable(), result.getEbikesAvailable());
        assertEquals(testStation.getDocksAvailable(), result.getDocksAvailable());
        assertEquals(testStation.getLatitude(), result.getLatitude());
        assertEquals(testStation.getLongitude(), result.getLongitude());
        assertEquals(testStation.getCapacity(), result.getCapacity());
        assertEquals(testStation.getInstalled(), result.getInstalled());
    }

    @Test
    @DisplayName("Mapping list of stations should return correctly mapped list when multiple stations in collection")
    void toResponseDTOCollection_CorrectMapping_ReturnsDTOList() {
        List<LiveStation> testStations = List.of(
            createTestLiveStation("test1"),
            createTestLiveStation("test2")
        );

        List<StationsResponseDTO> result = subject.toResponseDTOCollection(testStations);

        assertEquals(2, result.size());
        assertNotNull(result.get(0));
        assertNotNull(result.get(1));
        assertEquals(testStations.get(0).getStationId(), result.get(0).getStationId());
        assertEquals(testStations.get(1).getStationId(), result.get(1).getStationId());
    }

    @Test
    @DisplayName("Mapping list of stations should return empty list when input is empty")
    void toResponseDTOCollection_EmptyListInput_ReturnsEmptyList() {
        List<LiveStation> testStations = Collections.emptyList();

        List<StationsResponseDTO> result = subject.toResponseDTOCollection(testStations);

        assertEquals(0, result.size());
    }

    private LiveStation createTestLiveStation(String stationId) {
        LiveStation liveStation = new LiveStation();
        liveStation.setStationId(stationId);
        liveStation.setStationName("1st St");
        liveStation.setBikesAvailable(10);
        liveStation.setEbikesAvailable(6);
        liveStation.setDocksAvailable(5);
        liveStation.setInstalled(true);
        liveStation.setReturning(null);
        liveStation.setRenting(false);
        liveStation.setLatitude(70.35);
        liveStation.setLongitude(-70.35);
        liveStation.setCapacity(20);
        return liveStation;
    }
    
}
