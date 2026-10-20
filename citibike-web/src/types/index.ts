export type Station = {
    stationId: string;
    stationName: string;
    latitude: number;
    longitude: number;
    bikesAvailable: number;
    ebikesAvailable: number;
    docksAvailable: number;
    capacity: number;
    isRenting: boolean;
    isReturning: boolean;
    isInstalled: boolean;
};

export type HoverInfo = {
    x: number;
    y: number;
    name: string;
    bikes: number;
};

export type TopDestination = {
    rank: number;
    destinationStationId: string;
    destinationStationName: string;
    tripCount: number;
};

export type TopDestinationsResponse = {
    stationId: string;
    windowStart: string;
    windowEnd: string;
    generatedAt: string;
    destinations: TopDestination[];
};
