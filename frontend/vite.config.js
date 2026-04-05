import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(),tailwindcss()],
  server: {
    proxy: {
      // Reindirizza le chiamate che iniziano con /api al backend Python
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        // Rimuove il prefisso /api prima di inviare la richiesta al backend
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  }
})
