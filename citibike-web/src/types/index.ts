export type Station {
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
}