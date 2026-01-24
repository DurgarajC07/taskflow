// vite.config.js
import { defineConfig } from 'vite';
import tailwindcss from '@tailwindcss/vite';
// If using a framework like React, import its plugin too
import react from '@vitejs/plugin-react';
import path from 'path';
export default defineConfig({
  plugins: [
    react(), // Add your framework plugin here if needed
    tailwindcss(),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),  
    },
  },
  server: {
    port: 3000, 
    proxy: {
      '/api': {
        target: 'http://localhost:8000', 
        changeOrigin: true,
    },
  },
  },
});
