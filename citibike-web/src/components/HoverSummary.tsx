import type { HoverInfo } from '../types'

interface HoverSummaryProps {
    info: HoverInfo;
}

export default function HoverSummary({ info }: HoverSummaryProps) {
    return (
        <div
            className="absolute z-30 pointer-events-none bg-gray-900/90 text-white text-xs px-2.5 py-1.5 rounded shadow-lg transform -translate-x-1/2 -translate-y-full -mt-2 whitespace-nowrap"
            style={{ left: info.x, top: info.y }}
        >
            <p className="font-semibold">{info.name}</p>
            <p className="text-gray-300">{info.bikes} bikes available</p>
        </div>
    );
}