import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@app': path.resolve(__dirname, './src/app'),
      '@components': path.resolve(__dirname, './src/app/components'),
      '@hooks': path.resolve(__dirname, './src/app/hooks'),
      '@services': path.resolve(__dirname, './src/app/services'),
      '@store': path.resolve(__dirname, './src/app/store'),
      '@types': path.resolve(__dirname, './src/app/types'),
      '@utils': path.resolve(__dirname, './src/app/utils'),
      '@pages': path.resolve(__dirname, './src/pages'),
      '@styles': path.resolve(__dirname, './src/styles')
    }
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true
      }
    }
  }
})