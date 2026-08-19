package com.citibike.api.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.cache.CacheManager;
import org.springframework.cache.concurrent.ConcurrentMapCacheManager;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class CacheConfig {

    @Value("${citibike.stations.cache.name:station-status-cache}")
    private String cacheName;

    @Bean
    public CacheManager cacheManager() {
        return new ConcurrentMapCacheManager(cacheName);
    }
}
