import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import NewYorkMap from '../NewYorkMap';
import { useStations } from '../../hooks/useStations';

vi.mock('../../hooks/useStations', () => ({
    useStations: vi.fn(),
}));

vi.mock('react-map-gl/maplibre', () => ({
    default: ({ children, onClick, scrollZoom, dragPan }: { children: React.ReactNode; onClick?: (e: any) => void; scrollZoom?: boolean; dragPan?: boolean }) => (
        <div 
            data-testid="mock-map" 
            data-scroll-zoom={String(scrollZoom)}
            data-drag-pan={String(dragPan)}
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
                        isInstalled: true
                    }
                }]
            })}
        >
            {children}
        </div>
    ),
    Source: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
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

describe('NewYorkMap Component - Fixed Position & Geolocate Logic', () => {
    const mockRefetch = vi.fn();

    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('enables map panning and scrolling when no station is selected', () => {
        vi.mocked(useStations).mockReturnValue({
            stations: [],
            geoJsonData: { type: 'FeatureCollection', features: [] },
            isLoading: false,
            error: null,
            refetch: mockRefetch,
        });

        render(<NewYorkMap />);

        const mapContainer = screen.getByTestId('mock-map');
        expect(mapContainer).toHaveAttribute('data-scroll-zoom', 'true');
        expect(mapContainer).toHaveAttribute('data-drag-pan', 'true');
    });

    it('disables map scrolling and panning when a station is selected', async () => {
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
            }
        ];

        vi.mocked(useStations).mockReturnValue({
            stations: mockStations,
            geoJsonData: {
                type: 'FeatureCollection',
                features: [{
                    type: 'Feature',
                    id: 0,
                    geometry: { type: 'Point', coordinates: [-73.985, 40.748] },
                    properties: mockStations[0]
                }]
            },
            isLoading: false,
            error: null,
            refetch: mockRefetch,
        });

        render(<NewYorkMap />);

        // Click map to select station
        fireEvent.click(screen.getByTestId('mock-map'));

        await waitFor(() => {
            expect(screen.getByText('Test Station 1')).toBeInTheDocument();
        });

        const mapContainer = screen.getByTestId('mock-map');
        expect(mapContainer).toHaveAttribute('data-scroll-zoom', 'false');
        expect(mapContainer).toHaveAttribute('data-drag-pan', 'false');
    });

});