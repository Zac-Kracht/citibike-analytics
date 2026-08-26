import type { CircleLayer } from 'react-map-gl/maplibre';

export const stationsLayer: CircleLayer = {
    id: 'stations-layer',
    type: 'circle',
    source: 'stations',
    paint: {
        'circle-radius': [
            'interpolate', ['linear'], ['zoom'],
            10, 3,
            15, 8
        ],
        'circle-color': [
            'step',
            ['get', 'inventory'],
            '#ef4444', // 0 bikes: Red
            1, '#eab308', // 1 to 5 bikes: Yellow
            6, '#22c55e'  // 6+ bikes: Green
        ],
        'circle-stroke-width': 1.5,
        'circle-stroke-color': '#ffffff'
    }
};