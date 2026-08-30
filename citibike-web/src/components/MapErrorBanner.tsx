interface MapErrorBannerProps {
    message: string;
    onRetry: () => void;
}

export default function MapErrorBanner({ message, onRetry }: MapErrorBannerProps) {
    return (
        <div className="absolute top-6 left-1/2 transform -translate-x-1/2 bg-white px-5 py-3 rounded-lg shadow-[0_8px_30px_rgb(0,0,0,0.12)] border border-red-100 z-10 flex items-center gap-4 animate-in slide-in-from-top-4 duration-300">
            <div className="flex items-center gap-2 text-red-600">
                <svg 
                    width="20" 
                    height="20" 
                    viewBox="0 0 24 24" 
                    fill="none" 
                    stroke="currentColor" 
                    strokeWidth="2" 
                    strokeLinecap="round" 
                    strokeLinejoin="round"
                >
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="12" y1="8" x2="12" y2="12"></line>
                    <line x1="12" y1="16" x2="12.01" y2="16"></line>
                </svg>
                <p className="font-semibold text-sm">{message}</p>
            </div>
            
            <button 
                onClick={onRetry}
                className="px-3 py-1.5 bg-red-50 hover:bg-red-100 text-red-700 text-xs font-bold rounded-md transition-colors"
            >
                Try Again
            </button>
        </div>
    );
}