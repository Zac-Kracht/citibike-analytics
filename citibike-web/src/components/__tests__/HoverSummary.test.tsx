import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import HoverSummary from '../HoverSummary';
import type { HoverInfo } from '../../types';

describe('HoverSummary Component', () => {
    const mockHoverInfo: HoverInfo = {
        x: 150,
        y: 250,
        name: 'Central Park West & 72 St',
        bikes: 12,
    };

    it('renders the station name and available bike count correctly', () => {
        // Act
        render(<HoverSummary info={mockHoverInfo} />);

        // Assert
        expect(screen.getByText('Central Park West & 72 St')).toBeInTheDocument();
        expect(screen.getByText('12 bikes available')).toBeInTheDocument();
    });

    it('applies the correct absolute positioning style based on coordinates', () => {
        // Act
        render(<HoverSummary info={mockHoverInfo} />);

        // Assert
        const container = screen.getByText('Central Park West & 72 St').closest('div');
        expect(container).toHaveStyle({
            left: '150px',
            top: '250px',
        });
    });
});