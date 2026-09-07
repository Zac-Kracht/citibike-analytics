package com.citibike.api.controller;

import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;
import static org.hamcrest.Matchers.hasSize;

import java.util.Collections;
import java.util.List;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest;
import org.springframework.cache.CacheManager;
import org.springframework.http.MediaType;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

import com.citibike.api.service.StationsService;
import com.citibike.api.model.dto.StationsResponseDTO;

@WebMvcTest(StationsController.class)
public class StationsControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockitoBean
    private StationsService stationsService;

    @MockitoBean
    private CacheManager cacheManager;

    @Test
    @DisplayName("GET call returns list of stations when service response contains list of stations")
    void getStations_HappyPath_returnsList() throws Exception {
        List<StationsResponseDTO> stationsResponse = List.of(
            createStation("test1"),
            createStation("test2")
        );
        when(stationsService.getAllStations()).thenReturn(stationsResponse);

        mockMvc.perform(get("/api/v1/stations")
        .contentType(MediaType.APPLICATION_JSON))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$", hasSize(2)))
        .andExpect(jsonPath("$[0].stationId").value("test1"))
        .andExpect(jsonPath("$[1].stationId").value("test2"));
    }

    @Test
    @DisplayName("GET call returns empty list when service response contains no stations")
    void getStations_NoStations_returnsEmptyList() throws Exception {
        List<StationsResponseDTO> stationsResponse = Collections.emptyList();
        when(stationsService.getAllStations()).thenReturn(stationsResponse);

        mockMvc.perform(get("/api/v1/stations")
        .contentType(MediaType.APPLICATION_JSON))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$", hasSize(0)));
    }

    private StationsResponseDTO createStation(String stationId) {
        StationsResponseDTO station = new StationsResponseDTO();
        station.setStationId(stationId);
        station.setStationName("test");
        station.setBikesAvailable(1);
        station.setCapacity(10);
        return station;
    }
}
