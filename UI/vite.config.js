import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Proxy API calls to the FastAPI backend (default :8000) so the browser
// makes same-origin requests — avoids CORS without touching the backend.
// Override the target with VITE_BACKEND_URL if the backend runs elsewhere.
const BACKEND = process.env.VITE_BACKEND_URL ?? 'http://localhost:8000'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/negotiations': { target: BACKEND, changeOrigin: true },
      '/health': { target: BACKEND, changeOrigin: true },
    },
  },
})
