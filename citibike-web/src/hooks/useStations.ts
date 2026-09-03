import { useState, useEffect, useMemo, useCallback } from 'react';
import type { FeatureCollection } from 'geojson';
import type { Station } from '../types';


export function useStations() {
    const [stations, setStations] = useState<Station[]>([]);
    const [isLoading, setIsLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    const fetchStations = useCallback(async (isSilent = false) => {
        if (!isSilent) setIsLoading(true); // Only show loader on initial page load
        setError(null);

        try {
            const baseUrl = import.meta.env.VITE_GET_STATIONS_BASE_URL;
            const response = await fetch(`${baseUrl}/api/v1/stations`);

            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const data = await response.json();

            const validStations = data.filter((s: any) => s.latitude != null && s.longitude != null && s.isInstalled);
            setStations(validStations);
        } catch (err) {
            console.error("Failed to fetch stations:", err);
            setError("Unable to connect to the live network.");
        } finally {
            setIsLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchStations();
    }, []);

    useEffect(() => {
        const intervalId = setInterval(() => {
            fetchStations(true); // Pass true to fetch silently
        }, 60000); // 60 seconds

        return () => clearInterval(intervalId);
    }, [fetchStations]);

    const geoJsonData = useMemo<FeatureCollection>(() => {
        return {
            type: 'FeatureCollection',
            features: stations.map((station, idx) => ({
                type: 'Feature',
                id: idx,
                geometry: {
                    type: 'Point',
                    coordinates: [station.longitude, station.latitude]
                },
                properties: {
                    ...station,
                    inventory: station.bikesAvailable + station.ebikesAvailable
                }
            }))
        };
    }, [stations]);

    return { stations, geoJsonData, isLoading, error, refetch: fetchStations };
}