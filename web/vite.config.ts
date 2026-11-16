import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  // monaco-vim imports `monaco-editor/esm/vs/...`, which monaco-editor 0.57's exports map no longer allows.
  resolve: { alias: [{ find: /^monaco-editor\/esm\/vs\/(.*)$/, replacement: "monaco-editor/$1" }] },
  server: { port: 5173, proxy: { "/api": "http://localhost:4173" } },
});
