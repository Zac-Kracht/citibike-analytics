import { useState, useCallback, useRef } from 'react';
import Map, { Source, Layer, NavigationControl, GeolocateControl } from 'react-map-gl/maplibre';
import type { MapRef } from 'react-map-gl/maplibre';
import type { Station, HoverInfo } from '../types';
import { useStations } from '../hooks/useStations';
import { stationsLayer } from '../config/mapLayers';
import { NYC_BOUNDS, MAX_BOUNDS_ARRAY } from '../config/constants';
import StationSummaryPanel from './StationSummaryPanel';
import DataLoading from './DataLoading';
import MapErrorBanner from './MapErrorBanner';
import HoverSummary from './HoverSummary';
import LocationWarning from './LocationWarning';


export default function NewYorkMap() {
    const { geoJsonData, isLoading, error, refetch } = useStations();
    const [selectedStation, setSelectedStation] = useState<Station | null>(null);
    const [hoverInfo, setHoverInfo] = useState<HoverInfo | null>(null);
    const [locationWarning, setLocationWarning] = useState<string | null>(null);

    const mapRef = useRef<MapRef>(null);
    const hoveredFeatureId = useRef<string | null>(null);

    const mapStyleUrl = `https://api.maptiler.com/maps/streets-v2/style.json?key=${import.meta.env.VITE_MAPTILER_API_KEY}`;

    const onMapClick = useCallback((event: any) => {
        const feature = event.features?.[0];
        if (feature) {
            const station = feature.properties as Station;
            setSelectedStation(station);
            
            // Smoothly animate the map to center on the clicked station
            mapRef.current?.flyTo({
                center: [station.longitude, station.latitude],
                zoom: 15,
                duration: 1200 // 1.2 second animation
            });
        } else {
            setSelectedStation(null);
        }
    }, []);

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

    const handleGeolocate = useCallback((event: any) => {
        const userLng = event.coords.longitude;
        const userLat = event.coords.latitude;

        const isOutOfBounds = 
            userLng < NYC_BOUNDS.sw.lng || 
            userLng > NYC_BOUNDS.ne.lng || 
            userLat < NYC_BOUNDS.sw.lat || 
            userLat > NYC_BOUNDS.ne.lat;

        if (isOutOfBounds) {
            setLocationWarning("You appear to be outside the Citi Bike service area.");
            setTimeout(() => setLocationWarning(null), 5000);
        }
    }, []);

    return (
        <div className="w-full h-full relative flex overflow-hidden">
            <div className="flex-1 relative">
                {isLoading && <DataLoading/>}
                {error && <MapErrorBanner message={error} onRetry={refetch} />}
                {hoverInfo && <HoverSummary info={hoverInfo} />}
                {locationWarning && <LocationWarning message={locationWarning} onExitButtonClick={() => setLocationWarning(null)} />}
            
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
                        showUserHeading={true} 
                        onGeolocate={handleGeolocate}
                    />
            
                    <Source id="stations" type="geojson" data={geoJsonData}>
                        <Layer {...stationsLayer} />
                    </Source>
                </Map>
            </div>

            {selectedStation && (
                <StationSummaryPanel
                    station={selectedStation} 
                    onClose={() => setSelectedStation(null)} 
                />
            )}
            
        </div>
    );
}