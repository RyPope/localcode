import { fileURLToPath } from "node:url";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: [
      // Vite would pick monaco-vim's "browser" build, which inlines parts of an old Monaco (0.33).
      // Its ESM build imports our own monaco-editor instead.
      {
        find: /^monaco-vim$/,
        replacement: fileURLToPath(new URL("node_modules/monaco-vim/dist/index.mjs", import.meta.url)),
      },
      // monaco-vim imports `monaco-editor/esm/vs/...`, which monaco-editor 0.57's exports map no longer allows.
      { find: /^monaco-editor\/esm\/vs\/(.*)$/, replacement: "monaco-editor/$1" },
    ],
  },
  server: { port: 5173, proxy: { "/api": "http://localhost:4173" } },
});
