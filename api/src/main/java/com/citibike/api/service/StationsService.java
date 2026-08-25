package com.citibike.api.service;

import com.citibike.api.model.dto.StationsResponseDTO;
import java.util.List;

public interface StationsService {
    List<StationsResponseDTO> getAllStations();
    List<StationsResponseDTO> refreshStationCache();
}
