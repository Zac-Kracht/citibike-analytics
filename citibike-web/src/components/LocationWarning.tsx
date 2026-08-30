interface LocationWarningProps {
    message: string;
    onExitButtonClick: () => void;
}

export default function LocationWarning({ message, onExitButtonClick }: LocationWarningProps) {
    return (
        <div className="absolute top-6 left-1/2 transform -translate-x-1/2 bg-white px-5 py-3 rounded-lg shadow-[0_8px_30px_rgb(0,0,0,0.12)] border border-yellow-200 z-10 flex items-center gap-3 animate-in slide-in-from-top-4 duration-300">
            <svg className="text-yellow-500" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
                <line x1="12" y1="9" x2="12" y2="13"></line>
                <line x1="12" y1="17" x2="12.01" y2="17"></line>
            </svg>
            <p className="font-semibold text-sm text-gray-800">{message}</p>
            <button onClick={onExitButtonClick} className="ml-2 text-gray-400 hover:text-gray-600">
                ✕
            </button>
        </div>
    );
}