export const NYC_BOUNDS = {
    sw: { lng: -74.2855, lat: 40.5572 },
    ne: { lng: -73.6709, lat: 40.9661 }
};

export const MAX_BOUNDS_ARRAY = [
    [NYC_BOUNDS.sw.lng, NYC_BOUNDS.sw.lat],
    [NYC_BOUNDS.ne.lng, NYC_BOUNDS.ne.lat]
] as const;