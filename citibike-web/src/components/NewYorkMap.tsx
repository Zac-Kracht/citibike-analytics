import { useState, useCallback, useRef } from 'react';
import Map, { Source, Layer, NavigationControl } from 'react-map-gl/maplibre';
import type { MapRef } from 'react-map-gl/maplibre';
import { useStations } from '../hooks/useStations';
import { stationsLayer } from '../config/mapLayers';
import StationSummaryPanel from './StationSummaryPanel';
import type { Station } from '../types';


export default function NewYorkMap() {
    const { geoJsonData, isLoading, error } = useStations();
    const [selectedStation, setSelectedStation] = useState<Station | null>(null);
    const [hoverInfo, setHoverInfo] = useState<{
        x: number;
        y: number;
        name: string;
        bikes: number;
    } | null>(null);

    const mapRef = useRef<MapRef>(null);
    const hoveredFeatureId = useRef<string | null>(null);

    const mapStyleUrl = `https://api.maptiler.com/maps/streets-v2/style.json?key=${import.meta.env.VITE_MAPTILER_API_KEY}`; // TODO: secret

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

    return (
        // Flex container controls the layout between the Map and the Side Panel
        <div className="w-full h-full relative flex overflow-hidden">
            
            {/* The Map occupies all remaining space using flex-1 */}
            <div className="flex-1 relative">
                {isLoading && (
                    <div className="absolute top-4 left-1/2 transform -translate-x-1/2 bg-white px-4 py-2 rounded-md shadow-md z-10">
                        <p className="font-semibold text-gray-700">Loading live station data...</p>
                    </div>
                )}
            
                {error && (
                    <div className="absolute top-4 left-1/2 transform -translate-x-1/2 bg-red-100 border border-red-400 text-red-700 px-4 py-2 rounded-md shadow-md z-10">
                        <p className="font-semibold">Error: {error}</p>
                    </div>
                )}

                {hoverInfo && (
                    <div
                        className="absolute z-30 pointer-events-none bg-gray-900/90 text-white text-xs px-2.5 py-1.5 rounded shadow-lg transform -translate-x-1/2 -translate-y-full -mt-2 whitespace-nowrap"
                        style={{ left: hoverInfo.x, top: hoverInfo.y }}
                    >
                        <p className="font-semibold">{hoverInfo.name}</p>
                        <p className="text-gray-300">{hoverInfo.bikes} bikes available</p>
                    </div>
                )}
            
                <Map
                    ref={mapRef}
                    initialViewState={{
                        longitude: -73.985,
                        latitude: 40.748,
                        zoom: 12.5,
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
                >
                    <NavigationControl position="bottom-right" showCompass={false} />
            
                    <Source id="stations" type="geojson" data={geoJsonData}>
                        <Layer {...stationsLayer} />
                    </Source>
                </Map>
            </div>

            {/* The Side Panel renders on the right if a station is selected */}
            {selectedStation && (
                <StationSummaryPanel
                    station={selectedStation} 
                    onClose={() => setSelectedStation(null)} 
                />
            )}
            
        </div>
    );
}