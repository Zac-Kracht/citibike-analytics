import type { LayerProps } from 'react-map-gl/maplibre';

export const stationsLayer: LayerProps = {
    id: 'stations-layer',
    type: 'circle',
    source: 'stations',
    paint: {
        'circle-radius': [
            'interpolate', ['linear'], ['zoom'],
            10, ['case', ['boolean', ['feature-state', 'hover'], false], 6, 3],
            15, ['case', ['boolean', ['feature-state', 'hover'], false], 12, 8]
        ],
        'circle-color': [
            'case',
            ['boolean', ['get', 'isSelected'], false], '#f59e0b', // Selected origin: amber
            ['boolean', ['get', 'isDestination'], false], '#2563eb', // Top destinations: blue
            [
                'step',
                ['get', 'inventory'],
                '#ef4444', // 0 bikes: Red
                1, '#eab308', // 1 to 5 bikes: Yellow
                6, '#22c55e'  // 6+ bikes: Green
            ]
        ],
        'circle-stroke-width': ['case', ['boolean', ['feature-state', 'hover'], false], 3, 1.5],
        'circle-stroke-color': '#ffffff'
    }
};
