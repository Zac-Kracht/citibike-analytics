import { useState, useEffect } from 'react';
import Map, { Marker, Popup, NavigationControl } from 'react-map-gl/maplibre';

// The exact structure returned by your DynamoDB/API backend
interface Station {
  stationId: string;
  stationName: string;
  latitude: number;
  longitude: number;
  bikesAvailable: number;
  ebikesAvailable: number;
  docksAvailable: number;
  capacity: number;
  isRenting: boolean;
  isReturning: boolean;
  isInstalled: boolean;
}

export default function NewYorkMap() {
    const [stations, setStations] = useState<Station[]>([]);
    const [selectedStation, setSelectedStation] = useState<Station | null>(null);
    const [isLoading, setIsLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    const mapStyleUrl = `https://api.maptiler.com/maps/streets-v2/style.json?key=${import.meta.env.VITE_MAPTILER_API_KEY}`;

    useEffect(() => {
        const fetchStations = async () => {
          try {
            const response = await fetch('http://localhost:8080/api/v1/stations');
            
            if (!response.ok) {
              throw new Error(`HTTP error! status: ${response.status}`);
            }
            
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
    }, []); // Empty dependency array ensures this runs exactly once on mount

    const getPinColorClass = (bikesAvailable: number, ebikesAailable: number, capacity: number) => {
        const stationFill = (bikesAvailable + ebikesAailable) / capacity;
        if (stationFill === 0) return 'text-red-500';
        if (stationFill <= 0.25) return 'text-yellow-500';
        return 'text-green-500';
    };

    return (
        <div className="w-full h-full relative">
            {/* Optional: Simple loading indicator overlay */}
            {isLoading && (
                <div className="absolute top-4 left-1/2 transform -translate-x-1/2 bg-white px-4 py-2 rounded-md shadow-md z-10">
                <p className="font-semibold text-gray-700">Loading live station data...</p>
                </div>
            )}
        
            {/* Optional: Error state overlay */}
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
            >
                <NavigationControl position="bottom-right" showCompass={false} />
        
                {stations.map((station) => (
                    <Marker
                        key={station.stationId}
                        longitude={station.longitude}
                        latitude={station.latitude}
                        anchor="bottom" // Changed to bottom so the pin tip points exactly at the coordinate
                        onClick={(e) => {
                            e.originalEvent.stopPropagation();
                            setSelectedStation(station);
                        }}
                    >
                        <svg 
                            className={`w-4 h-4 ${getPinColorClass(station.bikesAvailable, station.ebikesAvailable, station.capacity)} drop-shadow-md cursor-pointer hover:scale-110 transition-transform origin-bottom`} 
                            viewBox="0 0 24 24" 
                            fill="currentColor" 
                            xmlns="http://www.w3.org/2000/svg"
                        >
                            <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z" />
                        </svg>
                    </Marker>
                ))}
        
                {selectedStation && (
                <Popup
                    longitude={selectedStation.longitude}
                    latitude={selectedStation.latitude}
                    anchor="bottom"
                    offset={12}
                    onClose={() => setSelectedStation(null)}
                    closeOnClick={false}
                    className="z-50"
                >
                    <div className="p-1 text-gray-800 min-w-[200px]">
                    <h3 className="font-bold text-md mb-2 leading-tight">{selectedStation.stationName}</h3>
                    <div className="flex justify-between text-sm">
                        <span>Classic:</span>
                        <span className="font-semibold">{selectedStation.bikesAvailable}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                        <span>E-Bikes:</span>
                        <span className="font-semibold">{selectedStation.ebikesAvailable}</span>
                    </div>
                    <div className="flex justify-between text-sm text-gray-500 mt-1 pt-1 border-t">
                        <span>Open Docks:</span>
                        <span className="font-semibold">{selectedStation.docksAvailable}</span>
                    </div>
                    </div>
                </Popup>
                )}
            </Map>
        </div>
    );
}