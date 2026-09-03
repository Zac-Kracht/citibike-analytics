export default function DataLoading() {
    return (
        <div className="absolute top-6 left-1/2 transform -translate-x-1/2 bg-white/95 backdrop-blur-sm px-5 py-2.5 rounded-full shadow-[0_4px_20px_rgba(0,0,0,0.15)] border border-gray-100 z-10 flex items-center gap-3 animate-in fade-in slide-in-from-top-4 duration-300">
            <svg className="animate-spin h-4 w-4 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span className="font-semibold text-gray-700 text-sm tracking-wide">Syncing live network...</span>
        </div>
    );
}