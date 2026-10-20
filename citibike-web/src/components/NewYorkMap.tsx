import { useState, useCallback, useRef, useEffect, useMemo } from 'react';
import Map, { Source, Layer, NavigationControl, GeolocateControl } from 'react-map-gl/maplibre';
import type { MapRef } from 'react-map-gl/maplibre';
import type { Station, HoverInfo } from '../types';
import { useStations } from '../hooks/useStations';
import { useTopDestinations } from '../hooks/useTopDestinations';
import { stationsLayer } from '../config/mapLayers';
import { MAX_BOUNDS_ARRAY } from '../config/constants';
import StationSummaryPanel from './StationSummaryPanel';
import DataLoading from './DataLoading';
import MapErrorBanner from './MapErrorBanner';
import HoverSummary from './HoverSummary';


export default function NewYorkMap() {
    const { stations, geoJsonData, isLoading, error, refetch } = useStations();
    const [selectedStation, setSelectedStation] = useState<Station | null>(null);
    const [hoverInfo, setHoverInfo] = useState<HoverInfo | null>(null);
    const {
        data: topDestinations,
        isLoading: isTopDestinationsLoading,
        error: topDestinationsError,
        refetch: refetchTopDestinations,
    } = useTopDestinations(selectedStation?.stationId ?? null);

    const mapRef = useRef<MapRef>(null);
    const hoveredFeatureId = useRef<string | null>(null);
    const viewportBeforeSelection = useRef<{
        center: [number, number];
        zoom: number;
        bearing: number;
        pitch: number;
    } | null>(null);
    const lastFramedSelection = useRef<string | null>(null);

    const mapStyleUrl = `https://api.maptiler.com/maps/streets-v2/style.json?key=${import.meta.env.VITE_MAPTILER_API_KEY}`;

    const destinationStationIds = useMemo(() => {
        if (!selectedStation || topDestinations?.stationId !== selectedStation.stationId) {
            return new Set<string>();
        }

        return new Set(
            topDestinations.destinations
                .slice(0, 5)
                .map(destination => destination.destinationStationId)
        );
    }, [selectedStation, topDestinations]);

    const visibleStations = useMemo(() => {
        if (!selectedStation) return stations;

        return stations.filter(station =>
            station.stationId === selectedStation.stationId ||
            destinationStationIds.has(station.stationId)
        );
    }, [stations, selectedStation, destinationStationIds]);

    const visibleStationIds = useMemo(
        () => new Set(visibleStations.map(station => station.stationId)),
        [visibleStations]
    );

    const visibleGeoJsonData = useMemo(() => ({
        ...geoJsonData,
        features: geoJsonData.features
            .filter(feature => visibleStationIds.has(String(feature.properties?.stationId)))
            .map(feature => {
                const stationId = String(feature.properties?.stationId);
                return {
                    ...feature,
                    properties: {
                        ...feature.properties,
                        isSelected: stationId === selectedStation?.stationId,
                        isDestination: destinationStationIds.has(stationId),
                    },
                };
            }),
    }), [geoJsonData, visibleStationIds, selectedStation, destinationStationIds]);

    const deselectStation = useCallback(() => {
        setSelectedStation(null);
        lastFramedSelection.current = null;

        const previousViewport = viewportBeforeSelection.current;
        if (previousViewport) {
            mapRef.current?.easeTo({
                ...previousViewport,
                duration: 900,
            });
        }
        viewportBeforeSelection.current = null;
    }, []);

    const handleDestinationHover = useCallback((stationId: string | null) => {
        if (!stationId) {
            setHoverInfo(null);
            return;
        }

        const station = stations.find(candidate => candidate.stationId === stationId);
        const map = mapRef.current?.getMap();
        if (!station || !map) return;

        const point = map.project([station.longitude, station.latitude]);
        setHoverInfo({
            x: point.x,
            y: point.y,
            name: station.stationName,
            bikes: station.bikesAvailable + station.ebikesAvailable,
        });
    }, [stations]);

    const handleDestinationSelect = useCallback((stationId: string) => {
        const station = stations.find(candidate => candidate.stationId === stationId);
        if (!station) return;

        setHoverInfo(null);
        setSelectedStation(station);
    }, [stations]);

    /** For auto refresh, make sure the selected station is still selected */
    useEffect(() => {
        if (selectedStation && stations.length > 0) {
            // Find the updated version of the currently selected station
            const updatedStation = stations.find(s => s.stationId === selectedStation.stationId);

            if (updatedStation && (
                updatedStation.bikesAvailable !== selectedStation.bikesAvailable ||
                updatedStation.ebikesAvailable !== selectedStation.ebikesAvailable
            )) {
                setSelectedStation(updatedStation);
            }
        }
    }, [stations, selectedStation]);

    useEffect(() => {
        if (!selectedStation) {
            lastFramedSelection.current = null;
            return;
        }
        if (isTopDestinationsLoading) return;

        const snapshotId = topDestinations?.generatedAt ?? 'no-destination-data';
        const selectionKey = `${selectedStation.stationId}:${snapshotId}`;
        if (lastFramedSelection.current === selectionKey) return;

        const stationsToFrame = visibleStations;
        if (stationsToFrame.length === 0) return;

        if (stationsToFrame.length === 1) {
            mapRef.current?.flyTo({
                center: [stationsToFrame[0].longitude, stationsToFrame[0].latitude],
                zoom: 14,
                duration: 1200,
            });
        } else {
            const longitudes = stationsToFrame.map(station => station.longitude);
            const latitudes = stationsToFrame.map(station => station.latitude);
            const bounds: [[number, number], [number, number]] = [
                [Math.min(...longitudes), Math.min(...latitudes)],
                [Math.max(...longitudes), Math.max(...latitudes)],
            ];

            mapRef.current?.fitBounds(bounds, {
                padding: 64,
                maxZoom: 14,
                duration: 1200,
            });
        }

        lastFramedSelection.current = selectionKey;
    }, [selectedStation, isTopDestinationsLoading, topDestinations, visibleStations]);

    const onMapClick = useCallback((event: any) => {
        const feature = event.features?.[0];
        if (feature) {
            const station = feature.properties as Station;

            if (selectedStation) {
                if (station.stationId === selectedStation.stationId) return;
                if (!destinationStationIds.has(station.stationId)) return;
            } else {
                const map = mapRef.current?.getMap();
                if (map) {
                    const center = map.getCenter();
                    viewportBeforeSelection.current = {
                        center: [center.lng, center.lat],
                        zoom: map.getZoom(),
                        bearing: map.getBearing(),
                        pitch: map.getPitch(),
                    };
                }
            }

            setSelectedStation(station);
        } else {
            if (selectedStation) deselectStation();
        }
    }, [selectedStation, destinationStationIds, deselectStation]);

    const onMouseMove = useCallback((event: any) => {
        const feature = event.features?.[0];
        const map = mapRef.current?.getMap();

        if (feature && map) {
            const currentStationId = feature.id;

            // If we moved to a new station, clear the hover state of the old one
            if (hoveredFeatureId.current !== null && hoveredFeatureId.current !== currentStationId) {
                map.setFeatureState(
                    { source: 'stations', id: hoveredFeatureId.current },
                    { hover: false }
                );
            }

            // Set the hover state for the new station
            hoveredFeatureId.current = currentStationId;
            map.setFeatureState(
                { source: 'stations', id: currentStationId },
                { hover: true }
            );

            // Update React tooltip state
            setHoverInfo({
                x: event.point.x,
                y: event.point.y,
                name: feature.properties.stationName,
                bikes: feature.properties.bikesAvailable + feature.properties.ebikesAvailable,
            });
        } else {
            // If the mouse is not over a station, clear everything
            if (hoveredFeatureId.current !== null && map) {
                map.setFeatureState(
                    { source: 'stations', id: hoveredFeatureId.current },
                    { hover: false }
                );
                hoveredFeatureId.current = null;
            }
            setHoverInfo(null);
        }
    }, []);

    const onMouseLeave = useCallback(() => {
        const map = mapRef.current?.getMap();
        if (hoveredFeatureId.current !== null && map) {
            map.setFeatureState(
                { source: 'stations', id: hoveredFeatureId.current },
                { hover: false }
            );
            hoveredFeatureId.current = null;
        }
        setHoverInfo(null);
    }, []);

    return (
        <div className="w-full h-full relative flex overflow-hidden">
            <div className="flex-1 relative">
                {isLoading && <DataLoading />}
                {error && <MapErrorBanner message={error} onRetry={refetch} />}
                {hoverInfo && <HoverSummary info={hoverInfo} />}

                <Map
                    ref={mapRef}
                    initialViewState={{
                        longitude: -73.985,
                        latitude: 40.748,
                        zoom: 11.5,
                        pitch: 0,
                        bearing: 0
                    }}
                    mapStyle={mapStyleUrl}
                    style={{ width: '100%', height: '100%' }}
                    interactiveLayerIds={['stations-layer']}
                    onClick={onMapClick}
                    onMouseMove={onMouseMove}
                    onMouseLeave={onMouseLeave}
                    cursor={hoverInfo ? "pointer" : "grab"}
                    minZoom={10}
                    maxBounds={MAX_BOUNDS_ARRAY}
                >
                    <NavigationControl position="bottom-right" showCompass={false} />

                    <GeolocateControl
                        position="bottom-right"
                        trackUserLocation={true}
                    />

                    <Source id="stations" type="geojson" data={visibleGeoJsonData}>
                        <Layer {...stationsLayer} />
                    </Source>
                </Map>
            </div>

            {selectedStation && (
                <StationSummaryPanel
                    station={selectedStation}
                    onClose={deselectStation}
                    topDestinations={topDestinations}
                    isTopDestinationsLoading={isTopDestinationsLoading}
                    topDestinationsError={topDestinationsError}
                    onRetryTopDestinations={refetchTopDestinations}
                    onDestinationHover={handleDestinationHover}
                    onSelectDestination={handleDestinationSelect}
                />
            )}

        </div>
    );
}
