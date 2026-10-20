import { act, renderHook, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { useTopDestinations } from '../useTopDestinations';
import type { TopDestinationsResponse } from '../../types';

const mockResponse: TopDestinationsResponse = {
    stationId: 'station-123',
    windowStart: '2026-07-01',
    windowEnd: '2026-10-01',
    generatedAt: '2026-10-15T06:12:00Z',
    destinations: [{
        rank: 1,
        destinationStationId: 'destination-1',
        destinationStationName: 'W 21 St & 6 Ave',
        tripCount: 1842,
    }],
};

describe('useTopDestinations', () => {
    beforeEach(() => {
        import.meta.env.VITE_CITIBIKE_API_BASE_URL = 'https://api.example.com/';
    });

    afterEach(() => {
        vi.restoreAllMocks();
        vi.unstubAllGlobals();
    });

    it('fetches the selected station endpoint and returns the response', async () => {
        const fetchMock = vi.fn().mockResolvedValue({
            ok: true,
            json: async () => mockResponse,
        } as Response);
        vi.stubGlobal('fetch', fetchMock);

        const { result } = renderHook(() => useTopDestinations('station-123'));

        await waitFor(() => expect(result.current.isLoading).toBe(false));

        expect(fetchMock).toHaveBeenCalledWith(
            'https://api.example.com/api/v1/stations/station-123/top-destinations',
            expect.objectContaining({ signal: expect.any(AbortSignal) })
        );
        expect(result.current.data).toEqual(mockResponse);
        expect(result.current.error).toBeNull();
    });

    it('does not fetch when no station is selected', () => {
        const fetchMock = vi.fn();
        vi.stubGlobal('fetch', fetchMock);

        const { result } = renderHook(() => useTopDestinations(null));

        expect(fetchMock).not.toHaveBeenCalled();
        expect(result.current).toMatchObject({
            data: null,
            isLoading: false,
            error: null,
        });
    });

    it('aborts the previous request when the selected station changes', async () => {
        const fetchMock = vi.fn((_url: string, options: RequestInit) => new Promise<Response>((_, reject) => {
            options.signal?.addEventListener('abort', () => reject(new DOMException('Aborted', 'AbortError')));
        }));
        vi.stubGlobal('fetch', fetchMock);

        const { rerender } = renderHook(
            ({ stationId }: { stationId: string | null }) => useTopDestinations(stationId),
            { initialProps: { stationId: 'station-123' } }
        );

        await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
        const firstSignal = fetchMock.mock.calls[0][1].signal;

        rerender({ stationId: 'station-456' });

        await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
        expect(firstSignal?.aborted).toBe(true);
    });

    it('exposes a retryable error when the API request fails', async () => {
        const fetchMock = vi.fn().mockResolvedValue({ ok: false, status: 500 } as Response);
        vi.stubGlobal('fetch', fetchMock);

        const { result } = renderHook(() => useTopDestinations('station-123'));
        await waitFor(() => expect(result.current.isLoading).toBe(false));

        expect(result.current.error).toBe('Unable to load top destinations.');

        fetchMock.mockResolvedValueOnce({
            ok: true,
            json: async () => mockResponse,
        } as Response);
        act(() => result.current.refetch());

        await waitFor(() => expect(result.current.data).toEqual(mockResponse));
    });
});
