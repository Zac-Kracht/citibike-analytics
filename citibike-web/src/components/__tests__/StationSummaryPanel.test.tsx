import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import StationSummaryPanel from '../StationSummaryPanel';
import type { Station, TopDestinationsResponse } from '../../types';

describe('StationSummaryPanel Component', () => {
    const mockStation: Station = {
        stationId: 'station-123',
        stationName: 'W 31 St & 7 Ave',
        bikesAvailable: 8,
        ebikesAvailable: 4,
        docksAvailable: 15,
        latitude: 40.75,
        longitude: -73.99,
        isInstalled: true,
        isRenting: true,
        isReturning: true,
        capacity: 17
    };

    const mockTopDestinations: TopDestinationsResponse = {
        stationId: 'station-123',
        windowStart: '2026-07-01',
        windowEnd: '2026-10-01',
        generatedAt: '2026-10-15T06:12:00Z',
        destinations: [
            {
                rank: 1,
                destinationStationId: 'destination-1',
                destinationStationName: 'W 21 St & 6 Ave',
                tripCount: 1842,
            },
            {
                rank: 2,
                destinationStationId: 'destination-2',
                destinationStationName: 'Broadway & W 24 St',
                tripCount: 1530,
            },
        ],
    };

    const defaultProps = {
        station: mockStation,
        onClose: vi.fn(),
        topDestinations: mockTopDestinations,
        isTopDestinationsLoading: false,
        topDestinationsError: null,
        onRetryTopDestinations: vi.fn(),
        onDestinationHover: vi.fn(),
        onSelectDestination: vi.fn(),
    };

    it('renders station name and live inventory counts correctly', () => {
        // Arrange
        const mockOnClose = vi.fn();

        // Act
        render(<StationSummaryPanel {...defaultProps} onClose={mockOnClose} />);

        // Assert
        expect(screen.getByText('W 31 St & 7 Ave')).toBeInTheDocument();
        expect(screen.getByText('Classic Bikes')).toBeInTheDocument();
        expect(screen.getByText('8')).toBeInTheDocument(); // bikesAvailable
        expect(screen.getByText('E-Bikes')).toBeInTheDocument();
        expect(screen.getByText('4')).toBeInTheDocument(); // ebikesAvailable
        expect(screen.getByText('Open Docks')).toBeInTheDocument();
        expect(screen.getByText('15')).toBeInTheDocument(); // docksAvailable
    });

    it('triggers the onClose callback when the close button is clicked', () => {
        // Arrange
        const mockOnClose = vi.fn();

        // Act
        render(<StationSummaryPanel {...defaultProps} onClose={mockOnClose} />);

        const closeButton = screen.getByRole('button', { name: /close panel/i });
        fireEvent.click(closeButton);

        // Assert
        expect(mockOnClose).toHaveBeenCalledTimes(1);
    });

    it('renders the destination names, ranks, counts, and coverage period', () => {
        render(<StationSummaryPanel {...defaultProps} />);

        expect(screen.getByText('Top 5 Destinations')).toBeInTheDocument();
        expect(screen.getByText('W 21 St & 6 Ave')).toBeInTheDocument();
        expect(screen.getByText('Broadway & W 24 St')).toBeInTheDocument();
        expect(screen.getByText('1,842 trips')).toBeInTheDocument();
        expect(screen.getByText('1,530 trips')).toBeInTheDocument();
        expect(screen.getByText(/Trips from/)).toBeInTheDocument();
    });

    it('shows the map hover and selects a destination when its tile is used', () => {
        render(<StationSummaryPanel {...defaultProps} />);

        const destinationButton = screen.getByRole('button', {
            name: 'Select destination W 21 St & 6 Ave',
        });
        fireEvent.mouseEnter(destinationButton);
        expect(defaultProps.onDestinationHover).toHaveBeenCalledWith('destination-1');

        fireEvent.click(destinationButton);
        expect(defaultProps.onSelectDestination).toHaveBeenCalledWith('destination-1');
    });

    it('renders loading, empty, and retryable error states', () => {
        const { rerender } = render(
            <StationSummaryPanel {...defaultProps} isTopDestinationsLoading />
        );
        expect(screen.getByRole('status')).toHaveTextContent('Loading top destinations');

        rerender(
            <StationSummaryPanel {...defaultProps} topDestinations={{
                ...mockTopDestinations,
                destinations: [],
            }} />
        );
        expect(screen.getByText(/No destination data is available/)).toBeInTheDocument();

        rerender(
            <StationSummaryPanel {...defaultProps} topDestinations={null} topDestinationsError="Unable to load top destinations." />
        );
        fireEvent.click(screen.getByRole('button', { name: 'Retry' }));
        expect(defaultProps.onRetryTopDestinations).toHaveBeenCalledTimes(1);
    });
});
