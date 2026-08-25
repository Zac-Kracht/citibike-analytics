package com.citibike.api.controller;

import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import com.citibike.api.model.dto.StationsResponseDTO;
import com.citibike.api.service.StationsService;

import java.util.List;

@RestController
@RequestMapping("/api/v1/stations")
@RequiredArgsConstructor
public class StationsController {

    private final StationsService stationsService;

    @GetMapping
    public ResponseEntity<List<StationsResponseDTO>> getStations() {
        List<StationsResponseDTO> stations = stationsService.getAllStations();
        return ResponseEntity.ok(stations);
    }
    
}
