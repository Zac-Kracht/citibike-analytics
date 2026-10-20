import { useCallback, useEffect, useState } from 'react';
import { getApiBaseUrl } from '../config/api';
import type { TopDestinationsResponse } from '../types';

type TopDestinationsState = {
    stationId: string | null;
    data: TopDestinationsResponse | null;
    isLoading: boolean;
    error: string | null;
};

const initialState: TopDestinationsState = {
    stationId: null,
    data: null,
    isLoading: false,
    error: null,
};

export function useTopDestinations(stationId: string | null) {
    const [state, setState] = useState<TopDestinationsState>(initialState);
    const [retryCount, setRetryCount] = useState(0);

    useEffect(() => {
        if (!stationId) {
            setState(initialState);
            return;
        }

        const selectedStationId = stationId;
        const controller = new AbortController();
        setState({ stationId: selectedStationId, data: null, isLoading: true, error: null });

        async function loadTopDestinations() {
            try {
                const response = await fetch(
                    `${getApiBaseUrl()}/api/v1/stations/${encodeURIComponent(selectedStationId)}/top-destinations`,
                    { signal: controller.signal }
                );

                if (!response.ok) {
                    throw new Error(
                        response.status === 404
                            ? 'Station not found.'
                            : 'Unable to load top destinations.'
                    );
                }

                const data = await response.json() as TopDestinationsResponse;
                setState({ stationId: selectedStationId, data, isLoading: false, error: null });
            } catch (error) {
                if (controller.signal.aborted) return;

                setState({
                    stationId: selectedStationId,
                    data: null,
                    isLoading: false,
                    error: error instanceof Error
                        ? error.message
                        : 'Unable to load top destinations.',
                });
            }
        }

        void loadTopDestinations();

        return () => controller.abort();
    }, [stationId, retryCount]);

    const refetch = useCallback(() => {
        if (stationId) setRetryCount(count => count + 1);
    }, [stationId]);

    // Avoid briefly showing the previous station's response before the new effect runs.
    const isCurrentStation = state.stationId === stationId;

    return {
        data: isCurrentStation ? state.data : null,
        isLoading: stationId !== null && (!isCurrentStation || state.isLoading),
        error: isCurrentStation ? state.error : null,
        refetch,
    };
}
