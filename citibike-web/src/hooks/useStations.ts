import { useState, useEffect, useMemo } from 'react';
import type { FeatureCollection } from 'geojson';
import type { Station } from '../types';


export function useStations() {
  const [stations, setStations] = useState<Station[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStations = async () => {
      try {
        const response = await fetch('http://localhost:8080/api/v1/stations'); // TODO: configure this as property
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

        const data = await response.json();
        const validStations = data.filter((s: any) => s.latitude != null && s.longitude != null && s.isInstalled);
        setStations(validStations);
      } catch (err) {
        console.error("Failed to fetch stations:", err);
        setError(err instanceof Error ? err.message : "Failed to load stations");
      } finally {
        setIsLoading(false);
      }
    };
    fetchStations();
  }, []);

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

  return { stations, geoJsonData, isLoading, error };
}