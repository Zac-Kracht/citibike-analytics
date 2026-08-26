import { Popup } from 'react-map-gl/maplibre';
import type { Station } from '../types';

interface StationPopupProps {
  station: Station;
  onClose: () => void;
}

export default function StationSidePanel({ station, onClose }: StationPopupProps) {
  return (
    <Popup
      longitude={station.longitude}
      latitude={station.latitude}
      anchor="bottom"
      offset={12}
      onClose={onClose}
      closeOnClick={false}
      className="z-50"
    >
      <div className="p-1 text-gray-800 min-w-[200px]">
        <h3 className="font-bold text-md mb-2 leading-tight">{station.stationName}</h3>
        <div className="flex justify-between text-sm">
          <span>Classic:</span>
          <span className="font-semibold">{station.bikesAvailable}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span>E-Bikes:</span>
          <span className="font-semibold">{station.ebikesAvailable}</span>
        </div>
        <div className="flex justify-between text-sm text-gray-500 mt-1 pt-1 border-t">
          <span>Open Docks:</span>
          <span className="font-semibold">{station.docksAvailable}</span>
        </div>
      </div>
    </Popup>
  );
}