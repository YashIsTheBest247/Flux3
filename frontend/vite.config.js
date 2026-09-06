import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vite.dev/config/
export default defineConfig({
    plugins: [react()],
    server: {
        port: 5173,
        proxy: {
            '/api': {
                target: 'http://127.0.0.1:8000',
                changeOrigin: true,
            },
            '/static': {
                target: 'http://127.0.0.1:8000',
                changeOrigin: true,
            },
            // The dashboard reads /health for the active profile and the
            // connected channel. It lives at the root rather than under /api,
            // so without this it would 404 against the dev server itself and
            // the header would silently show nothing connected.
            '/health': {
                target: 'http://127.0.0.1:8000',
                changeOrigin: true,
            },
            '/ping': {
                target: 'http://127.0.0.1:8000',
                changeOrigin: true,
            },
        },
    },
});
