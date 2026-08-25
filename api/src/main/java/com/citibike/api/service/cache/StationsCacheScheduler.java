package com.citibike.api.service.cache;

import com.citibike.api.service.StationsService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

@Slf4j
@Component
@RequiredArgsConstructor
public class StationsCacheScheduler {

    private final StationsService stationsService;

    /**
     * Populate the cache immediately on application startup.
     */
    @EventListener(ApplicationReadyEvent.class)
    public void onStartup() {
        log.info("Initializing station status cache on application launch...");
        try {
            stationsService.refreshStationCache();
            log.info("Stations cache successfully initialized.");
        } catch (Exception e) {
            log.error("Failed to initialize cache: {}", e.getMessage(), e);
        }
    }

    /**
     * Poll DynamoDB on a fixed delay configured by properties.
     */
    @Scheduled(fixedDelayString = "${citibike.stations.dynamo.poll.rate-ms}")
    public void scheduleCacheRefresh() {
        try {
            stationsService.refreshStationCache();
        } catch (Exception e) {
            log.error("Failed to refresh cache: {}", e.getMessage(), e);
        }
    }
}
