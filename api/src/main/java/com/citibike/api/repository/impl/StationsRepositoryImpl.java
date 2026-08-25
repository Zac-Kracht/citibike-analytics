package com.citibike.api.repository.impl;

import com.citibike.api.model.entity.LiveStation;
import com.citibike.api.repository.StationsRepository;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Repository;
import software.amazon.awssdk.enhanced.dynamodb.DynamoDbEnhancedClient;
import software.amazon.awssdk.enhanced.dynamodb.DynamoDbTable;
import software.amazon.awssdk.enhanced.dynamodb.TableSchema;
import software.amazon.awssdk.services.dynamodb.DynamoDbClient;

import java.util.List;
import java.util.stream.Collectors;

@Slf4j
@Repository
public class StationsRepositoryImpl implements StationsRepository {

    private final DynamoDbTable<LiveStation> stationsTable;

    public StationsRepositoryImpl(
        DynamoDbClient dynamoDbClient,
        @Value("${aws.dynamodb.table-name}") String tableName
    ) {
        
        DynamoDbEnhancedClient enhancedClient = DynamoDbEnhancedClient.builder()
            .dynamoDbClient(dynamoDbClient)
            .build();

        TableSchema<LiveStation> stationSchema = TableSchema.fromBean(LiveStation.class);

        this.stationsTable = enhancedClient.table(tableName, stationSchema);
    }

    @Override
    public List<LiveStation> fetchAllStations() {
        log.info("Scanning DynamoDB table: {}", stationsTable.tableName());
        return stationsTable.scan()
            .items()
            .stream()
            .collect(Collectors.toList());
    }
    
}
