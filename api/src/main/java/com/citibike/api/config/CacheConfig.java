package com.citibike.api.config;

import org.springframework.cache.CacheManager;
import org.springframework.cache.concurrent.ConcurrentMapCacheManager;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class CacheConfig {

    private final String cacheName = "station-status-cache";

    @Bean
    public CacheManager cacheManager() {
        return new ConcurrentMapCacheManager(cacheName);
    }
}
