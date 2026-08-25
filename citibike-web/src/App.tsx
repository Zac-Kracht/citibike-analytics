import NewYorkMap from "./components/NewYorkMap"
import { setWorkerUrl } from 'maplibre-gl';
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url';

setWorkerUrl(workerUrl);

function App() {
  return (
    <main className="h-screen w-screen">
      <NewYorkMap />
    </main>
  );
}

export default App
