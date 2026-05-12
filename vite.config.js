import { defineConfig } from 'vite';
import { resolve } from 'path';

export default defineConfig({
  // Đặt root tại thư mục gốc của dự án
  root: resolve('./'),
  base: '/static/',
  server: {
    port: 5173,
    strictPort: true,
    host: 'localhost',
    origin: 'http://localhost:5173',
    hmr: {
        overlay: true
    }
  },
  build: {
    outDir: resolve('./static/dist'),
    assetsDir: '',
    manifest: true,
    rollupOptions: {
      input: {
        main: resolve('./static/js/main.js'),
        base: resolve('./static/css/base.css')
      }
    }
  }
});
