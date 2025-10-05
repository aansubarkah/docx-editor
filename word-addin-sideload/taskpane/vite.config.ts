import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import mkcert from 'vite-plugin-mkcert'

export default defineConfig({
  plugins: [vue(), mkcert()],
  server: { https: true, host: 'localhost', port: 5173 },
  build: { outDir: 'dist' },
})
