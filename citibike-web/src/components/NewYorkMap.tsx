import { useState, useCallback } from 'react';
import Map, { Source, Layer, NavigationControl } from 'react-map-gl/maplibre';
import { useStations } from '../hooks/useStations';
import { stationsLayer } from '../config/mapLayers';
import StationSidePanel from './StationSidePanel';
import type { Station } from '../types';

export default function NewYorkMap() {
    const { geoJsonData, isLoading, error } = useStations();
    const [selectedStation, setSelectedStation] = useState<Station | null>(null);

    const mapStyleUrl = `https://api.maptiler.com/maps/streets-v2/style.json?key=${import.meta.env.VITE_MAPTILER_API_KEY}`;

    const onMapClick = useCallback((event: any) => {
        const feature = event.features?.[0];
        if (feature) {
            setSelectedStation(feature.properties as Station);
        } else {
            setSelectedStation(null);
        }
    }, []);

    return (
        <div className="w-full h-full relative">
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
        
            <Map
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
                cursor="pointer"
            >
                <NavigationControl position="bottom-right" showCompass={false} />
        
                <Source id="stations" type="geojson" data={geoJsonData}>
                    <Layer {...stationsLayer} />
                </Source>
        
                {selectedStation && (
                    <StationSidePanel 
                        station={selectedStation} 
                        onClose={() => setSelectedStation(null)} 
                    />
                )}
            </Map>
        </div>
    );
}