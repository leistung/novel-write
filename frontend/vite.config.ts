import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// Docker 部署时通过 VITE_PROXY_TARGET=http://backend:8000 指向容器网络内的 backend；
// 本机直接 npm run dev 时默认 localhost:8000。
const proxyTarget = process.env.VITE_PROXY_TARGET || 'http://localhost:8000'

export default defineConfig({
  plugins: [react()],
  resolve: { alias: { '@': path.resolve(__dirname, './src') } },
  server: {
    host: true,
    port: 5173,
    proxy: { '/api': { target: proxyTarget, changeOrigin: true } },
  },
  build: {
    rollupOptions: {
      output: {
        // 手动拆 vendor：首屏只加载 react 核心，编辑器/图表等按需
        manualChunks(id) {
          if (id.includes('node_modules')) {
            if (id.includes('@tiptap') || id.includes('tiptap')) return 'editor'
            if (id.includes('@tanstack/react-query')) return 'query'
            if (id.includes('axios')) return 'http'
            if (
              id.includes('react-dom') ||
              id.includes('react-router') ||
              id.includes('react/') ||
              id.includes('scheduler')
            ) {
              return 'react-vendor'
            }
            if (id.includes('zustand')) return 'state'
            return 'vendor'
          }
        },
      },
    },
  },
})
