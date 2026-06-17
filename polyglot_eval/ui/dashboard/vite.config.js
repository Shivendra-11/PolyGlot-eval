import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { existsSync } from 'node:fs'
import { resolve, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const dataJs = resolve(__dirname, 'src/data.js')
const dataStub = resolve(__dirname, 'src/data.stub.js')

export default defineConfig({
  plugins: [
    react(),
    {
      name: 'polyglot-dashboard-data',
      resolveId(source, importer) {
        if (source !== './data.js' || !importer) return null
        if (!importer.includes('dashboard/src')) return null
        return existsSync(dataJs) ? dataJs : dataStub
      },
    },
  ],
  server: { port: 5175, open: true },
})
