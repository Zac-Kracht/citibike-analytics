export function getApiBaseUrl(): string {
    return (import.meta.env.VITE_CITIBIKE_API_BASE_URL ?? '').replace(/\/+$/, '');
}
