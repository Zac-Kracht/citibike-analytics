package com.citibike.api.mapper;

import com.citibike.api.model.dto.StationsResponseDTO;
import com.citibike.api.model.entity.LiveStation;

import java.util.List;

import org.mapstruct.Mapper;

@Mapper(componentModel = "spring")
public interface StationMapper {
    StationsResponseDTO toResponseDTO(LiveStation station);
    List<StationsResponseDTO> toResponseDTOCollection(List<LiveStation> stations);
}
