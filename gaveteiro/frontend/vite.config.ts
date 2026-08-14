import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// base './' é obrigatório: o Ingress do Home Assistant serve o app sob um
// prefixo dinâmico, então nenhum caminho pode ser absoluto.
// O build sai direto em backend/app/static, que o FastAPI serve.
export default defineConfig({
  plugins: [react()],
  base: './',
  build: {
    outDir: '../backend/app/static',
    emptyOutDir: true,
  },
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:8099',
    },
  },
})
