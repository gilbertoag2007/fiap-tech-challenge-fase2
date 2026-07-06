import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    // Proxy usado apenas por `npm run dev` — não afeta o build de produção
    // (dist/), que usa VITE_API_URL (ver src/config.js) para montar a URL da API.
    proxy: {
      '/rotas': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
      '/auth': 'http://localhost:8000',
    },
  },
})
