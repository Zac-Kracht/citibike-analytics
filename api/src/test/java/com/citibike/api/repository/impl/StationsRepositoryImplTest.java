package com.citibike.api.repository.impl;

import com.citibike.api.model.entity.LiveStation;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.test.util.ReflectionTestUtils;
import software.amazon.awssdk.core.pagination.sync.SdkIterable;
import software.amazon.awssdk.enhanced.dynamodb.DynamoDbTable;
import software.amazon.awssdk.enhanced.dynamodb.model.PageIterable;
import software.amazon.awssdk.services.dynamodb.DynamoDbClient;

import java.util.List;
import java.util.stream.Stream;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
public class StationsRepositoryImplTest {

    @Mock
    private DynamoDbClient dynamoDbClient;

    @Mock
    private DynamoDbTable<LiveStation> stationsTable;

    @Mock
    private PageIterable<LiveStation> pageIterable;

    @Mock
    private SdkIterable<LiveStation> itemsIterable;

    private StationsRepositoryImpl subject;

    @BeforeEach
    void setUp() {
        subject = new StationsRepositoryImpl(dynamoDbClient, "test-table-name");
        ReflectionTestUtils.setField(subject, "stationsTable", stationsTable);
    }

    @Test
    @DisplayName("fetchAllStations should return list of LiveStations when data is available in DynamoDB")
    void fetchAllStations_SuccessfulScan_ReturnsList() {
        LiveStation station1 = new LiveStation();
        LiveStation station2 = new LiveStation();
        
        when(stationsTable.tableName()).thenReturn("test-table-name");
        when(stationsTable.scan()).thenReturn(pageIterable);
        when(pageIterable.items()).thenReturn(itemsIterable);
        when(itemsIterable.stream()).thenReturn(Stream.of(station1, station2));

        List<LiveStation> result = subject.fetchAllStations();

        assertNotNull(result);
        assertEquals(2, result.size());
        verify(stationsTable).tableName();
        verify(stationsTable).scan();
    }
    
    @Test
    @DisplayName("fetchAllStations should return an empty list when no data is found in DynamoDB")
    void fetchAllStations_EmptyScan_ReturnsEmptyList() {
        when(stationsTable.tableName()).thenReturn("test-table-name");
        when(stationsTable.scan()).thenReturn(pageIterable);
        when(pageIterable.items()).thenReturn(itemsIterable);
        when(itemsIterable.stream()).thenReturn(Stream.empty());

        List<LiveStation> result = subject.fetchAllStations();

        assertNotNull(result);
        assertTrue(result.isEmpty());
        verify(stationsTable).tableName();
        verify(stationsTable).scan();
    }
}