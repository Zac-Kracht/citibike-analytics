import type { Station } from '../types';

interface StationSummaryProps {
  station: Station;
  onClose: () => void;
}

export default function StationSummaryPanel({ station, onClose }: StationSummaryProps) {
  return (
    <div className="w-80 md:w-96 h-full bg-white shadow-[-4px_0_20px_rgba(0,0,0,0.1)] flex flex-col z-20 overflow-y-auto shrink-0 animate-in slide-in-from-right-8 duration-300">
      {/* Header */}
      <div className="flex justify-between items-start p-6 border-b border-gray-100">
        <h2 className="text-xl font-bold text-gray-800 leading-tight pr-4">
          {station.stationName}
        </h2>
        <button 
          onClick={onClose} 
          className="p-1.5 hover:bg-gray-100 rounded-full text-gray-500 hover:text-gray-800 transition-colors"
          aria-label="Close panel"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
      </div>

      <div className="p-6 flex flex-col gap-8">
        {/* Live Inventory Section */}
        <section>
          <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">Live Inventory</h3>
          <div className="bg-gray-50 rounded-xl p-4 space-y-3 border border-gray-100">
            <div className="flex justify-between items-center">
              <span className="text-gray-600 font-medium">Classic Bikes</span>
              <span className="font-bold text-lg text-gray-800">{station.bikesAvailable}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600 font-medium">E-Bikes</span>
              <span className="font-bold text-lg text-gray-800">{station.ebikesAvailable}</span>
            </div>
            <div className="pt-3 border-t border-gray-200 flex justify-between items-center">
              <span className="text-gray-600 font-medium">Open Docks</span>
              <span className="font-bold text-lg text-gray-800">{station.docksAvailable}</span>
            </div>
          </div>
        </section>

        {/* Top Destinations Placeholder */}
        <section>
          <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">Top 5 Destinations</h3>
          <div className="bg-blue-50/50 border border-blue-100 border-dashed rounded-xl p-6 text-center">
            <p className="text-blue-600 font-medium text-sm">Feature coming soon</p>
          </div>
        </section>

        {/* Daily Average Use Placeholder */}
        <section>
          <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">Daily Average Use</h3>
          <div className="bg-blue-50/50 border border-blue-100 border-dashed rounded-xl p-6 text-center">
            <p className="text-blue-600 font-medium text-sm">Feature coming soon</p>
          </div>
        </section>
      </div>
    </div>
  );
}