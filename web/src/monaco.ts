// Bundle Monaco locally (no CDN): localcode must work offline once imported.
import { loader } from "@monaco-editor/react";
import * as monaco from "monaco-editor";
import EditorWorker from "monaco-editor/esm/vs/editor/editor.worker?worker";

self.MonacoEnvironment = { getWorker: () => new EditorWorker() };

monaco.editor.defineTheme("localcode-dark", {
  base: "vs-dark",
  inherit: true,
  rules: [],
  colors: {
    "editor.background": "#0F1215",
    "editor.lineHighlightBackground": "#161B21",
    "editorGutter.background": "#0F1215",
  },
});
monaco.editor.defineTheme("localcode-light", {
  base: "vs",
  inherit: true,
  rules: [],
  colors: { "editor.background": "#FCFCFD", "editor.lineHighlightBackground": "#F2F4F8" },
});

loader.config({ monaco });

export { monaco };
