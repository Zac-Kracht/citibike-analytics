import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import MapErrorBanner from '../MapErrorBanner';

describe('MapErrorBanner Component', () => {
    it('renders the custom error message correctly', () => {
        // Arrange
        const errorMessage = 'Unable to connect to the live network.';
        const mockOnRetry = vi.fn();

        // Act
        render(<MapErrorBanner message={errorMessage} onRetry={mockOnRetry} />);

        // Assert
        expect(screen.getByText(errorMessage)).toBeInTheDocument();
    });

    it('triggers the onRetry callback function when the Try Again button is clicked', () => {
        // Arrange
        const errorMessage = 'Network error occurred';
        const mockOnRetry = vi.fn();

        // Act
        render(<MapErrorBanner message={errorMessage} onRetry={mockOnRetry} />);
        
        const retryButton = screen.getByRole('button', { name: /try again/i });
        fireEvent.click(retryButton);

        // Assert
        expect(mockOnRetry).toHaveBeenCalledTimes(1);
    });
});