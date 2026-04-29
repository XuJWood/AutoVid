import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    port: 8362,
    proxy: {
      '/api': {
        target: 'http://localhost:8010',
        changeOrigin: true
      },
      '/media': {
        target: 'http://localhost:8010',
        changeOrigin: true
      }
    },
    // Allow large video files to be loaded
    fs: {
      allow: ['..']
    }
  }
})
