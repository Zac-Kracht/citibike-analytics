package com.citibike.api.controller;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;

import java.util.List;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.resttestclient.TestRestTemplate;
import org.springframework.boot.resttestclient.autoconfigure.AutoConfigureTestRestTemplate;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.testcontainers.containers.GenericContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

import com.citibike.api.model.dto.StationsResponseDTO;
import com.citibike.api.model.entity.LiveStation;
import com.citibike.api.service.cache.StationsCacheScheduler;

import software.amazon.awssdk.enhanced.dynamodb.DynamoDbEnhancedClient;
import software.amazon.awssdk.enhanced.dynamodb.DynamoDbTable;
import software.amazon.awssdk.enhanced.dynamodb.TableSchema;
import software.amazon.awssdk.services.dynamodb.DynamoDbClient;
import software.amazon.awssdk.services.dynamodb.model.DeleteTableRequest;
import software.amazon.awssdk.services.dynamodb.model.ResourceNotFoundException;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@AutoConfigureTestRestTemplate
@Testcontainers
public class StationsControllerIT {

    private static final int DYNAMODB_PORT = 8000;
    private static final String LIVE_STATIONS_TABLE = "live-stations-test";
    
    @Container
    static GenericContainer<?> dynamoDb = new GenericContainer<>("amazon/dynamodb-local:latest")
            .withExposedPorts(DYNAMODB_PORT);

    @DynamicPropertySource
    static void configureProperties(DynamicPropertyRegistry registry) {
        String endpoint = String.format("http://%s:%d", dynamoDb.getHost(), dynamoDb.getMappedPort(8000));
        
        registry.add("aws.dynamodb.endpoint-override", () -> endpoint);
        registry.add("aws.dynamodb.table-name", () -> LIVE_STATIONS_TABLE);
        registry.add("aws.region", () -> "us-east-1");
        registry.add("aws.access-key-id", () -> "test-key");
        registry.add("aws.secret-access-key", () -> "test-secret");
    }

    @Autowired
    private DynamoDbClient dynamoDbClient;

    @Autowired
    private TestRestTemplate restTemplate;

    @MockitoBean
    private StationsCacheScheduler scheduler;

    private DynamoDbTable<LiveStation> stationsTable;

    @BeforeEach
    void setUp() {
        DynamoDbEnhancedClient enhancedClient = DynamoDbEnhancedClient.builder()
                .dynamoDbClient(dynamoDbClient)
                .build();
        
        stationsTable = enhancedClient.table(LIVE_STATIONS_TABLE, TableSchema.fromBean(LiveStation.class));

        // Recreate the table before each test to guarantee a pristine database state
        deleteTableIfExists();
        createTable();
    }

    private void createTable() {
        stationsTable.createTable();
    }

    private void deleteTableIfExists() {
        try {
            dynamoDbClient.deleteTable(DeleteTableRequest.builder()
                    .tableName(LIVE_STATIONS_TABLE)
                    .build());
        } catch (ResourceNotFoundException e) {
            // Ignored if table does not yet exist
        }
    }

    @Test
    @DisplayName("GET /api/v1/stations request should successfully fetch records from containerized DynamoDB")
    void getStations_IntegrationTest() {
        LiveStation station = new LiveStation();
        station.setStationId("station-101");
        station.setStationName("Grand Central Station");
        stationsTable.putItem(station);

        ResponseEntity<List<StationsResponseDTO>> response = restTemplate.exchange(
            "/api/v1/stations", 
            HttpMethod.GET,
            null,
            new ParameterizedTypeReference<List<StationsResponseDTO>>() {}
        );

        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertNotNull(response.getBody());
        assertEquals(1, response.getBody().size());
        assertEquals("station-101", response.getBody().get(0).getStationId());
    }
}
