import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import DataLoading from '../DataLoading';

describe('DataLoading Component', () => {
    it('renders the syncing live network message correctly', () => {
        // Act
        render(<DataLoading />);

        // Assert
        const loadingText = screen.getByText('Syncing live network...');
        expect(loadingText).toBeInTheDocument();
        expect(loadingText).toHaveClass('font-semibold', 'text-gray-700');
    });

    it('renders the loading spinner SVG animation', () => {
        // Act
        render(<DataLoading />);

        // Assert - verify the SVG element exists and contains the spin class
        const spinnerSvg = document.querySelector('svg');
        expect(spinnerSvg).toBeInTheDocument();
        expect(spinnerSvg).toHaveClass('animate-spin');
    });
});