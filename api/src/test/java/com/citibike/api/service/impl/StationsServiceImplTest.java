package com.citibike.api.service.impl;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.util.Collections;
import java.util.List;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mapstruct.factory.Mappers;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import com.citibike.api.mapper.StationMapper;
import com.citibike.api.model.dto.StationsResponseDTO;
import com.citibike.api.model.entity.LiveStation;
import com.citibike.api.repository.StationsRepository;

@ExtendWith(MockitoExtension.class)
public class StationsServiceImplTest {

    @Mock
    private StationsRepository stationsRepository;

    private StationMapper stationMapper = Mappers.getMapper(StationMapper.class);

    private StationsServiceImpl subject;

    private LiveStation mockLiveStation;

    private String STATION_TEST_ID = "abc123";
    private String STATION_TEST_NAME = "Test Station";

    @BeforeEach
    void setUp() {
        mockLiveStation = new LiveStation();
        mockLiveStation.setStationId(STATION_TEST_ID);
        mockLiveStation.setStationName(STATION_TEST_NAME);

        subject = new StationsServiceImpl(stationsRepository, stationMapper);
    }

    @Test
    @DisplayName("Get stations should return valid list when live stations are fetched and mapped")
    void getAllStations_ValidMapping_ReturnsList() {
        List<LiveStation> mockLiveStations = List.of(mockLiveStation);

        when(stationsRepository.fetchAllStations()).thenReturn(mockLiveStations);

        List<StationsResponseDTO> result = subject.getAllStations();

        assertEquals(result.size(), 1);
        assertEquals(result.get(0).getStationId(), STATION_TEST_ID);
        assertEquals(result.get(0).getStationName(), STATION_TEST_NAME);

        verify(stationsRepository, times(1)).fetchAllStations();
    }

    @Test
    @DisplayName("Get stations should return empty list when live stations are empty")
    void getAllStations_EmptyLiveStations_ReturnsEmptyList() {
        List<LiveStation> mockLiveStations = Collections.emptyList();

        when(stationsRepository.fetchAllStations()).thenReturn(mockLiveStations);

        List<StationsResponseDTO> result = subject.getAllStations();

        assertEquals(result.size(), 0);

        verify(stationsRepository, times(1)).fetchAllStations();
    }

    @Test
    @DisplayName("Cache refresh should return valid list when live stations are fetched and mapped")
    void refreshStationCache_ValidMapping_ReturnsList() {
        List<LiveStation> mockLiveStations = List.of(mockLiveStation);

        when(stationsRepository.fetchAllStations()).thenReturn(mockLiveStations);

        List<StationsResponseDTO> result = subject.refreshStationCache();

        assertEquals(result.size(), 1);
        assertEquals(result.get(0).getStationId(), STATION_TEST_ID);
        assertEquals(result.get(0).getStationName(), STATION_TEST_NAME);

        verify(stationsRepository, times(1)).fetchAllStations();
    }
    
}
