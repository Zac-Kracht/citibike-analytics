package com.citibike.api.repository;

import com.citibike.api.model.entity.LiveStation;
import java.util.List;

public interface StationsRepository {
    List<LiveStation> fetchAllStations();
}
