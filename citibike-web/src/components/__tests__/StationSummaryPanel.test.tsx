import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import StationSummaryPanel from '../StationSummaryPanel';
import type { Station } from '../../types';

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

    it('renders station name and live inventory counts correctly', () => {
        // Arrange
        const mockOnClose = vi.fn();

        // Act
        render(<StationSummaryPanel station={mockStation} onClose={mockOnClose} />);

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
        render(<StationSummaryPanel station={mockStation} onClose={mockOnClose} />);

        const closeButton = screen.getByRole('button', { name: /close panel/i });
        fireEvent.click(closeButton);

        // Assert
        expect(mockOnClose).toHaveBeenCalledTimes(1);
    });
});