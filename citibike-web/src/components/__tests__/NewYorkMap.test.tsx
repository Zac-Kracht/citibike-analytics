import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import NewYorkMap from '../NewYorkMap';
import { useStations } from '../../hooks/useStations';
import { useTopDestinations } from '../../hooks/useTopDestinations';
import type { TopDestinationsResponse } from '../../types';

vi.mock('../../hooks/useStations', () => ({
    useStations: vi.fn(),
}));

vi.mock('../../hooks/useTopDestinations', () => ({
    useTopDestinations: vi.fn(),
}));

vi.mock('react-map-gl/maplibre', () => ({
    default: ({ children, onClick }: { children: React.ReactNode; onClick?: (e: any) => void }) => (
        <div 
            data-testid="mock-map" 
            onClick={() => onClick?.({
                features: [{
                    properties: {
                        stationId: 'station-1',
                        stationName: 'Test Station 1',
                        bikesAvailable: 5,
                        ebikesAvailable: 2,
                        docksAvailable: 10,
                        latitude: 40.748,
                        longitude: -73.985,
                        isInstalled: true,
                        isRenting: true,
                        isReturning: true,
                        capacity: 17
                    }
                }]
            })}
        >
            {children}
        </div>
    ),
    Source: ({ children, data }: { children: React.ReactNode; data: { features: Array<{ properties?: { stationId?: string } }> } }) => (
        <div data-testid="station-source" data-station-ids={data.features.map(feature => feature.properties?.stationId).join(',')}>
            {children}
        </div>
    ),
    Layer: () => <div data-testid="mock-layer" />,
    NavigationControl: () => <div data-testid="mock-nav-control" />,
    GeolocateControl: ({ onGeolocate }: { onGeolocate?: () => void }) => (
        <button 
            data-testid="mock-geolocate-control" 
            onClick={() => onGeolocate?.()}
        >
            Geolocate
        </button>
    ),
}));

describe('NewYorkMap station selection', () => {
    const mockRefetch = vi.fn();

    beforeEach(() => {
        vi.clearAllMocks();
        vi.mocked(useTopDestinations).mockReturnValue({
            data: null,
            isLoading: false,
            error: null,
            refetch: vi.fn(),
        });
    });

    it('shows every station before a station is selected', () => {
        vi.mocked(useStations).mockReturnValue({
            stations: [
                { stationId: 'station-1' },
                { stationId: 'station-2' },
                { stationId: 'station-3' },
            ] as never,
            geoJsonData: {
                type: 'FeatureCollection',
                features: [
                    { type: 'Feature', id: 0, geometry: { type: 'Point', coordinates: [-73.98, 40.74] }, properties: { stationId: 'station-1' } },
                    { type: 'Feature', id: 1, geometry: { type: 'Point', coordinates: [-73.97, 40.75] }, properties: { stationId: 'station-2' } },
                    { type: 'Feature', id: 2, geometry: { type: 'Point', coordinates: [-73.96, 40.76] }, properties: { stationId: 'station-3' } },
                ],
            },
            isLoading: false,
            error: null,
            refetch: mockRefetch,
        });

        render(<NewYorkMap />);

        expect(screen.getByTestId('station-source')).toHaveAttribute(
            'data-station-ids',
            'station-1,station-2,station-3'
        );
    });

    it('shows only the selected station and its top destinations', async () => {
        const mockStations = [
            {
                stationId: 'station-1',
                stationName: 'Test Station 1',
                bikesAvailable: 5,
                ebikesAvailable: 2,
                docksAvailable: 10,
                latitude: 40.748,
                longitude: -73.985,
                isInstalled: true,
                isRenting: true,
                isReturning: true,
                capacity: 17
            },
            {
                stationId: 'station-2',
                stationName: 'Destination Station',
                bikesAvailable: 4,
                ebikesAvailable: 1,
                docksAvailable: 12,
                latitude: 40.75,
                longitude: -73.98,
                isInstalled: true,
                isRenting: true,
                isReturning: true,
                capacity: 17,
            },
            {
                stationId: 'station-3',
                stationName: 'Unrelated Station',
                bikesAvailable: 3,
                ebikesAvailable: 1,
                docksAvailable: 13,
                latitude: 40.76,
                longitude: -73.97,
                isInstalled: true,
                isRenting: true,
                isReturning: true,
                capacity: 17,
            },
        ];

        const destinationResponse: TopDestinationsResponse = {
            stationId: 'station-1',
            windowStart: '2026-07-01',
            windowEnd: '2026-10-01',
            generatedAt: '2026-10-15T06:12:00Z',
            destinations: [{
                rank: 1,
                destinationStationId: 'station-2',
                destinationStationName: 'Destination Station',
                tripCount: 100,
            }],
        };
        vi.mocked(useTopDestinations).mockReturnValue({
            data: destinationResponse,
            isLoading: false,
            error: null,
            refetch: vi.fn(),
        });

        vi.mocked(useStations).mockReturnValue({
            stations: mockStations,
            geoJsonData: {
                type: 'FeatureCollection',
                features: mockStations.map((station, id) => ({
                    type: 'Feature' as const,
                    id,
                    geometry: { type: 'Point' as const, coordinates: [station.longitude, station.latitude] },
                    properties: station,
                }))
            },
            isLoading: false,
            error: null,
            refetch: mockRefetch,
        });

        render(<NewYorkMap />);

        // Click map to select station
        fireEvent.click(screen.getByTestId('mock-map'));

        expect(useTopDestinations).toHaveBeenLastCalledWith('station-1');

        await waitFor(() => {
            expect(screen.getByText('Test Station 1')).toBeInTheDocument();
        });

        await waitFor(() => {
            expect(screen.getByTestId('station-source')).toHaveAttribute(
                'data-station-ids',
                'station-1,station-2'
            );
        });

        fireEvent.click(screen.getByRole('button', {
            name: 'Select destination Destination Station',
        }));

        await waitFor(() => {
            expect(useTopDestinations).toHaveBeenLastCalledWith('station-2');
            expect(screen.getByText('Destination Station')).toBeInTheDocument();
        });
    });

});
