import { renderHook, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useStations } from '../useStations';

describe('useStations Hook', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        // Mock environment variable used in useStations
        import.meta.env.VITE_GET_STATIONS_BASE_URL = 'http://localhost:3000';
    });

    afterEach(() => {
        vi.restoreAllMocks();
    });

    it('initializes with loading state true, empty stations, and null error', () => {
        // Arrange - mock fetch to pending/delayed response so we capture initial mounting state
        vi.stubGlobal('fetch', vi.fn().mockImplementationOnce(() => new Promise(() => {})));

        // Act
        const { result } = renderHook(() => useStations());

        // Assert
        expect(result.current.isLoading).toBe(true);
        expect(result.current.stations).toEqual([]);
        expect(result.current.error).toBeNull();
        expect(result.current.geoJsonData).toEqual({
            type: 'FeatureCollection',
            features: []
        });
    });

    it('fetches and filters stations successfully (ignoring uninstalled or null coordinates)', async () => {
        // Arrange
        const mockApiResponse = [
            { stationId: '1', stationName: 'Valid Station', latitude: 40.7, longitude: -73.9, isInstalled: true, bikesAvailable: 5, ebikesAvailable: 2, docksAvailable: 10 },
            { stationId: '2', stationName: 'Null Lat', latitude: null, longitude: -73.9, isInstalled: true, bikesAvailable: 3, ebikesAvailable: 1, docksAvailable: 5 },
            { stationId: '3', stationName: 'Not Installed', latitude: 40.8, longitude: -74.0, isInstalled: false, bikesAvailable: 2, ebikesAvailable: 0, docksAvailable: 8 }
        ];

        vi.stubGlobal('fetch', vi.fn().mockResolvedValueOnce({
            ok: true,
            json: async () => mockApiResponse,
        } as Response));

        // Act
        const { result } = renderHook(() => useStations());

        // Wait until loading finishes
        await waitFor(() => {
            expect(result.current.isLoading).toBe(false);
        });

        // Assert - only the valid station should remain after filtering
        expect(result.current.error).toBeNull();
        expect(result.current.stations).toHaveLength(1);
        expect(result.current.stations[0].stationName).toBe('Valid Station');

        // Assert GeoJSON formatting
        expect(result.current.geoJsonData.features).toHaveLength(1);
        expect(result.current.geoJsonData.features[0].properties).toMatchObject({
            stationName: 'Valid Station',
            inventory: 7 // bikesAvailable (5) + ebikesAvailable (2)
        });
    });

    it('handles API failure and sets the proper error state', async () => {
        // Arrange
        vi.stubGlobal('fetch', vi.fn().mockResolvedValueOnce({
            ok: false,
            status: 500,
        } as Response));

        // Act
        const { result } = renderHook(() => useStations());

        // Wait until loading finishes
        await waitFor(() => {
            expect(result.current.isLoading).toBe(false);
        });

        // Assert
        expect(result.current.stations).toEqual([]);
        expect(result.current.error).toBe('Unable to connect to the live network.');
    });
});