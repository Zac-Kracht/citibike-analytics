import { http, HttpResponse } from 'msw';
import type { Station } from '../types/index';

const STATIONS_DATA = [
  // --- Manhattan ---
  { name: 'Broadway & W 51 St', lat: 40.762288, lng: -73.983362 },
  { name: 'E 17 St & Broadway', lat: 40.737050, lng: -73.990093 },
  { name: 'W 21 St & 6 Ave', lat: 40.741740, lng: -73.994156 },
  { name: '1 Ave & E 68 St', lat: 40.765005, lng: -73.958185 },
  { name: 'W 41 St & 8 Ave', lat: 40.756405, lng: -73.990026 },
  { name: 'E 47 St & Park Ave', lat: 40.755103, lng: -73.974987 },
  { name: 'Cleveland Pl & Spring St', lat: 40.722533, lng: -73.997170 },
  { name: '8 Ave & W 31 St', lat: 40.750585, lng: -73.994685 },
  { name: 'Grand St & Elizabeth St', lat: 40.718822, lng: -73.995960 },
  { name: 'W 14 St & The High Line', lat: 40.743184, lng: -74.008588 },
  { name: 'Pike St & Monroe St', lat: 40.711738, lng: -73.991930 },
  { name: 'E 11 St & 2 Ave', lat: 40.729720, lng: -73.987330 },
  { name: 'Christopher St & Greenwich St', lat: 40.732916, lng: -74.007114 },
  { name: 'W 33 St & 7 Ave', lat: 40.750200, lng: -73.990930 },
  { name: 'E 84 St & Park Ave', lat: 40.778627, lng: -73.957721 },
  { name: 'W 72 St & Columbus Ave', lat: 40.777490, lng: -73.978110 },
  { name: 'E 2 St & Avenue B', lat: 40.722174, lng: -73.983688 },
  { name: 'Centre St & Chambers St', lat: 40.712733, lng: -74.004607 },
  { name: 'W 110 St & Cathedral Pkwy', lat: 40.802816, lng: -73.961021 },
  { name: 'Mercer St & Bleecker St', lat: 40.727064, lng: -73.996621 },
  { name: 'E 33 St & 1 Ave', lat: 40.743227, lng: -73.974498 },
  { name: 'W 54 St & 9 Ave', lat: 40.766468, lng: -73.987216 },
  { name: 'Barclay St & Church St', lat: 40.712435, lng: -74.008880 },
  { name: 'E 60 St & 2 Ave', lat: 40.761227, lng: -73.962820 },
  { name: 'W 84 St & Broadway', lat: 40.787120, lng: -73.977110 },

  // --- Brooklyn ---
  { name: 'Cadman Plaza West & Montague St', lat: 40.693830, lng: -73.990539 },
  { name: 'Bedford Ave & S 9 St', lat: 40.710451, lng: -73.960876 },
  { name: 'Atlantic Ave & Fort Greene Pl', lat: 40.683826, lng: -73.976365 },
  { name: 'Grand Ave & Bergen St', lat: 40.680611, lng: -73.962418 },
  { name: 'Metropolitan Ave & Bedford Ave', lat: 40.715098, lng: -73.959223 },
  { name: 'Jay St & York St', lat: 40.701214, lng: -73.986841 },
  { name: 'Wythe Ave & N 13 St', lat: 40.721644, lng: -73.957930 },
  { name: 'Flushing Ave & Carlton Ave', lat: 40.697883, lng: -73.973500 },
  { name: 'Union St & Nevins St', lat: 40.679124, lng: -73.987730 },
  { name: 'Clinton Ave & Myrtle Ave', lat: 40.693261, lng: -73.968896 },
  { name: 'Smith St & 9 St', lat: 40.673898, lng: -73.996380 },
  { name: '3 Ave & 11 St', lat: 40.672450, lng: -73.991210 },
  { name: 'Nassau Ave & Russell St', lat: 40.725570, lng: -73.948240 },
  { name: 'Franklin Ave & Empire Blvd', lat: 40.663140, lng: -73.957230 },
  { name: 'Classon Ave & St Marks Ave', lat: 40.676520, lng: -73.959810 },
  { name: '4 Ave & 9 St', lat: 40.670580, lng: -73.988710 },
  { name: 'Manhattan Ave & Greenpoint Ave', lat: 40.730260, lng: -73.953940 },
  { name: 'DeKalb Ave & Vanderbilt Ave', lat: 40.689410, lng: -73.968850 },
  { name: 'Graham Ave & Herbert St', lat: 40.719290, lng: -73.944680 },
  { name: 'Hoyt St & Warren St', lat: 40.685980, lng: -73.989240 },
  { name: 'Washington Ave & Park Ave', lat: 40.696100, lng: -73.967530 },
  { name: 'Driggs Ave & N 9 St', lat: 40.718130, lng: -73.955320 },
  { name: 'Bond St & Fulton St', lat: 40.689620, lng: -73.983050 },
  { name: 'S 5 St & Kent Ave', lat: 40.714200, lng: -73.966020 },
  { name: 'Boerum Pl & Pacific St', lat: 40.689210, lng: -73.988220 },

  // --- Jersey City ---
  { name: 'Grove St PATH - Newark Ave & Grove St', lat: 40.719586, lng: -74.043117 },
  { name: 'Exchange Pl PATH - Christopher Columbus Dr', lat: 40.716801, lng: -74.033320 },
  { name: 'Hoboken Terminal - Hudson St & Hudson Pl', lat: 40.735938, lng: -74.030305 },
  { name: 'Newport PATH - Washington Blvd & 6 St', lat: 40.727223, lng: -74.033759 },
  { name: 'Journal Square PATH - Sip Ave & Summit Ave', lat: 40.733012, lng: -74.062900 },
  { name: 'Washington St & 1 St - Hoboken', lat: 40.737831, lng: -74.030700 },
  { name: '14 St & Washington St - Hoboken', lat: 40.751840, lng: -74.026640 },
  { name: 'Hamilton Park - 8 St & Jersey Ave', lat: 40.727590, lng: -74.044230 },
  { name: 'Liberty State Park Light Rail', lat: 40.710150, lng: -74.052850 },
  { name: 'Grand St & Washington St - Jersey City', lat: 40.715490, lng: -74.038240 },
];

/**
 * Helper to generate capacity & inventory numbers for mock stations
 */
function generateMockStations(): Station[] {
  return STATIONS_DATA.map((loc, idx) => {
    // Total capacity between 15 and 45 docks
    const capacity = 15 + ((idx * 7) % 31);
    
    const bikesAvailable = Math.floor(capacity * (0.2 + ((idx * 3) % 40) / 100));
    const ebikesAvailable = Math.floor(capacity * (0.1 + ((idx * 5) % 25) / 100));
    const docksAvailable = Math.max(0, capacity - bikesAvailable - ebikesAvailable);

    return {
      stationId: `station-${idx + 1}`,
      stationName: loc.name,
      latitude: loc.lat,
      longitude: loc.lng,
      bikesAvailable,
      ebikesAvailable,
      docksAvailable,
      capacity,
      isInstalled: true,
      isRenting: true,
      isReturning: true,
    };
  });
}

export const handlers = [
  http.get<never, never, Station[]>('http://localhost:8080/api/v1/stations', () => {
    return HttpResponse.json(generateMockStations());
  }),
];
