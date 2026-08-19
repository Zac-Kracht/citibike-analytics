package com.citibike.api.controller;

import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.time.Instant;
import java.util.Map;

@RestController
@RequestMapping("/actuator/health")
@RequiredArgsConstructor
public class HealthController {

    @GetMapping
    public ResponseEntity<Map<String, Object>> getHealth() {
        Map<String, Object> status = Map.of(
            "status", "UP",
            "timestamp", Instant.now().toString(),
            "service", "citibike-api"
        );
        return ResponseEntity.ok(status);
    }
}