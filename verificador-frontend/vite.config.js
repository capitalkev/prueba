import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'https://orquestador-service-598125168090.southamerica-west1.run.app',
        changeOrigin: true,
      }
    }
  }
});