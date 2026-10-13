import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import 'maplibre-gl/dist/maplibre-gl.css';

async function enableMocking(): Promise<ServiceWorkerRegistration | undefined> {
    if (import.meta.env.MODE !== 'development') {
        return;
    }

    const { worker } = await import('./mocks/browser');
    return worker.start();
}


enableMocking().then(() => {
    createRoot(document.getElementById('root')!).render(
        <App />
    );
});
