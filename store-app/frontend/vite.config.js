import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// The Store shopfront runs on port 5173.
export default defineConfig({
  plugins: [react()],
  server: { port: 5173 },
})
