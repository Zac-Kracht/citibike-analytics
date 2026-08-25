import { useState } from 'react';
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
}

// Sample stations scattered around NYC
const SAMPLE_STATIONS: Station[] = [
  {
    stationId: "66dcac42-0aca-11e7-82f6-3863bb44ef7c",
    stationName: "Kent Ave & N 7 St",
    latitude: 40.72036775298455,
    longitude: -73.96165072917938,
    bikesAvailable: 73,
    ebikesAvailable: 14,
    docksAvailable: 2,
    capacity: 79,
    isRenting: true,
    isReturning: true
  },
  {
    stationId: "66db237e-0aca-11e7-82f6-3863bb44ef7c",
    stationName: "W 21 St & 6 Ave",
    latitude: 40.74174,
    longitude: -73.994156,
    bikesAvailable: 12,
    ebikesAvailable: 5,
    docksAvailable: 40,
    capacity: 57,
    isRenting: true,
    isReturning: true
  },
  {
    stationId: "66db6aae-0aca-11e7-82f6-3863bb44ef7c",
    stationName: "Broadway & W 60 St",
    latitude: 40.76915505,
    longitude: -73.98191841,
    bikesAvailable: 0,
    ebikesAvailable: 2,
    docksAvailable: 31,
    capacity: 33,
    isRenting: true,
    isReturning: true
  }
];

export default function NewYorkMap() {
  const [selectedStation, setSelectedStation] = useState<Station | null>(null);
  const mapStyleUrl = `https://api.maptiler.com/maps/streets-v2/style.json?key=${import.meta.env.VITE_MAPTILER_API_KEY}`;

  return (
    <div className="w-full h-full relative">
      <Map
        initialViewState={{
          longitude: -73.985, // Centered on Manhattan
          latitude: 40.748,
          zoom: 12.5,
          pitch: 0,
          bearing: 0
        }}
        mapStyle={mapStyleUrl}
        style={{ width: '100%', height: '100%' }}
      >
        <NavigationControl position="bottom-right" showCompass={false} />
        {/* Render Station Pins */}
        {SAMPLE_STATIONS.map((station) => (
          <Marker
            key={station.stationId}
            longitude={station.longitude}
            latitude={station.latitude}
            anchor="center"
            onClick={(e) => {
              // Prevent click from propagating to the map canvas
              e.originalEvent.stopPropagation();
              setSelectedStation(station);
            }}
          >
            {/* Simple dot marker that scales on hover */}
            <div className="w-4 h-4 bg-blue-600 border-2 border-white rounded-full shadow-md cursor-pointer hover:scale-125 transition-transform" />
          </Marker>
        ))}

        {/* Render Popup if a station is clicked */}
        {selectedStation && (
          <Popup
            longitude={selectedStation.longitude}
            latitude={selectedStation.latitude}
            anchor="bottom"
            offset={12} // Offset to not cover the pin
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