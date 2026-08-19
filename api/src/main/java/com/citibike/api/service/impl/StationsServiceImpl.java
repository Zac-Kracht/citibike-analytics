package com.citibike.api.service.impl;

import com.citibike.api.repository.StationsRepository;
import com.citibike.api.service.StationsService;
import com.citibike.api.mapper.StationMapper;
import com.citibike.api.model.dto.StationsResponseDTO;
import com.citibike.api.model.entity.LiveStation;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.cache.annotation.CachePut;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;

import java.util.List;

@Slf4j
@Service
@RequiredArgsConstructor
public class StationsServiceImpl implements StationsService {

    private final StationsRepository stationsRepository;
    private final StationMapper stationMapper;

    @Override
    @Cacheable(value = "${citibike.cache.name:station-status-cache}", key = "'all_stations'")
    public List<StationsResponseDTO> getAllStations() {
        log.info("Cache miss: fetching station status directly from DynamoDB...");
        return this.retrieveStationsAsDTO();
    }

    @Override
    @CachePut(value = "${citibike.cache.name:station-status-cache}", key = "'all_stations'")
    public List<StationsResponseDTO> refreshStationCache() {
        log.info("Polling DynamoDB to update station cache...");
        return this.retrieveStationsAsDTO();
    }

    private List<StationsResponseDTO> retrieveStationsAsDTO() {
        List<LiveStation> liveStations = stationsRepository.fetchAllStations();
        return stationMapper.toResponseDTOCollection(liveStations);
    }
    
}
