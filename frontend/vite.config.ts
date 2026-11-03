// this forwads /api to the backend during development
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react()],
  server: {
    // In development the API runs separately on :8000. Proxying it keeps the browser on one origin,
    // so the session cookie works without cross-site settings.
    proxy: { '/api': 'http://localhost:8000' },
  },
})
