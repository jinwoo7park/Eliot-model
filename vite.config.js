import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath } from 'url'
import { dirname, resolve } from 'path'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

// https://vitejs.dev/config/
export default defineConfig({
  // root는 기본값 사용 (index.html과 같은 디렉토리)
  plugins: [react()],
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    rollupOptions: {
      input: resolve(__dirname, 'index.html'),
    },
  },
  // 개발 서버 설정은 로컬 개발 환경에서만 사용
  // Railway에서는 백엔드가 정적 파일을 서빙하므로 프록시 불필요
  server: process.env.NODE_ENV === 'development' ? {
    host: '0.0.0.0',
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  } : undefined
})
