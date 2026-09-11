import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig(({ command }) => ({
  plugins: [vue()],

  // 生产环境：前端静态文件由 FastAPI 在 /static 路径下提供
  base: command === 'serve' ? '/' : '/static/',

  build: {
    outDir: resolve(__dirname, '../converter/static'),
    emptyOutDir: true,
  },

  server: {
    port: 8080,
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
    },
  },
}))
