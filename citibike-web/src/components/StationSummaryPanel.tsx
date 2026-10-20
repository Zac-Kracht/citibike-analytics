import type { Station, TopDestinationsResponse } from '../types';

interface StationSummaryProps {
  station: Station;
  onClose: () => void;
  topDestinations: TopDestinationsResponse | null;
  isTopDestinationsLoading: boolean;
  topDestinationsError: string | null;
  onRetryTopDestinations: () => void;
  onDestinationHover: (stationId: string | null) => void;
  onSelectDestination: (stationId: string) => void;
}

export default function StationSummaryPanel({
  station,
  onClose,
  topDestinations,
  isTopDestinationsLoading,
  topDestinationsError,
  onRetryTopDestinations,
  onDestinationHover,
  onSelectDestination,
}: StationSummaryProps) {
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

        {/* Top Destinations Section */}
        <section>
          <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">Top 5 Destinations</h3>
          {isTopDestinationsLoading ? (
            <p className="text-sm text-gray-500" role="status" aria-live="polite">
              Loading top destinations…
            </p>
          ) : topDestinationsError ? (
            <div className="rounded-xl border border-red-100 bg-red-50 p-4 text-sm text-red-700" role="alert">
              <p>{topDestinationsError}</p>
              <button
                type="button"
                onClick={onRetryTopDestinations}
                className="mt-2 font-semibold underline underline-offset-2"
              >
                Retry
              </button>
            </div>
          ) : topDestinations && topDestinations.destinations.length > 0 ? (
            <>
              <ol className="space-y-3" aria-label="Top destinations">
                {topDestinations.destinations.slice(0, 5).map(destination => (
                  <li key={`${destination.rank}-${destination.destinationStationId}`}>
                    <button
                      type="button"
                      aria-label={`Select destination ${destination.destinationStationName}`}
                      onMouseEnter={() => onDestinationHover(destination.destinationStationId)}
                      onMouseLeave={() => onDestinationHover(null)}
                      onFocus={() => onDestinationHover(destination.destinationStationId)}
                      onBlur={() => onDestinationHover(null)}
                      onClick={() => onSelectDestination(destination.destinationStationId)}
                      className="group flex w-full items-start gap-3 rounded-xl border border-gray-100 bg-gray-50 p-3 text-left transition-colors hover:border-blue-200 hover:bg-blue-50 focus-visible:border-blue-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400"
                    >
                      <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-blue-100 text-xs font-bold text-blue-700 transition-colors group-hover:bg-blue-200">
                        {destination.rank}
                      </span>
                      <span className="min-w-0 flex-1 text-sm font-medium text-gray-800 group-hover:text-blue-900">
                        {destination.destinationStationName}
                      </span>
                      <span className="shrink-0 text-xs text-gray-500">
                        {destination.tripCount.toLocaleString()} trips
                      </span>
                    </button>
                  </li>
                ))}
              </ol>
              <p className="mt-3 text-xs text-gray-500">
                Trips from {formatDate(topDestinations.windowStart)} through{' '}
                {formatExclusiveEndDate(topDestinations.windowEnd)}.
              </p>
            </>
          ) : (
            <p className="rounded-xl bg-gray-50 p-4 text-sm text-gray-500">
              No destination data is available for this station yet.
            </p>
          )}
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

function formatDate(date: string): string {
  return new Date(`${date}T00:00:00`).toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

function formatExclusiveEndDate(date: string): string {
  const lastIncludedDay = new Date(`${date}T00:00:00`);
  lastIncludedDay.setDate(lastIncludedDay.getDate() - 1);
  return lastIncludedDay.toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}
