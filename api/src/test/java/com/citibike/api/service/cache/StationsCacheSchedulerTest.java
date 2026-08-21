package com.citibike.api.service.cache;

import static org.junit.jupiter.api.Assertions.assertDoesNotThrow;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.util.Collections;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import com.citibike.api.service.StationsService;

@ExtendWith(MockitoExtension.class)
public class StationsCacheSchedulerTest {

    @Mock
    private StationsService stationsService;

    @InjectMocks
    private StationsCacheScheduler subject;

    @Test
    @DisplayName("Scheduled task should successfully refresh station cache")
    void scheduleCacheRefresh_ReturnsSuccessfully() {
        when(stationsService.refreshStationCache()).thenReturn(Collections.emptyList());
        subject.scheduleCacheRefresh();
        verify(stationsService, times(1)).refreshStationCache();
    }

    @Test
    @DisplayName("Scheduled task should successfully exit gracefully when exception is thrown")
    void scheduleCacheRefresh_ExceptionThrown_ReturnGracefully() {
        when(stationsService.refreshStationCache()).thenThrow(new RuntimeException("bad"));
        assertDoesNotThrow(() -> subject.scheduleCacheRefresh());
    }
    
}
