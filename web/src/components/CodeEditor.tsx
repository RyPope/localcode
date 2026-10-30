import Editor, { type OnMount } from "@monaco-editor/react";
import { useEffect, useRef } from "react";
import type { Lang } from "../api";
import { MONACO_LANG, monaco } from "../monaco";
import { useTheme } from "../useTheme";

export default function CodeEditor({
  lang,
  value,
  onChange,
  fontSize,
  onRun,
  onSubmit,
}: {
  lang: Lang;
  value: string;
  onChange: (v: string) => void;
  fontSize: number;
  onRun: () => void;
  onSubmit: () => void;
}) {
  const theme = useTheme();
  // Monaco registers commands once; keep the latest callbacks in refs.
  const actions = useRef({ onRun, onSubmit });
  useEffect(() => {
    actions.current = { onRun, onSubmit };
  }, [onRun, onSubmit]);

  const onMount: OnMount = (editor) => {
    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, () => actions.current.onRun());
    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyMod.Shift | monaco.KeyCode.Enter, () =>
      actions.current.onSubmit(),
    );
    editor.focus();
  };

  return (
    <Editor
      value={value}
      language={MONACO_LANG[lang]}
      theme={theme === "light" ? "localcode-light" : "localcode-dark"}
      onChange={(v) => onChange(v ?? "")}
      onMount={onMount}
      options={{
        fontSize,
        fontFamily: "Geist Mono, ui-monospace, monospace",
        minimap: { enabled: false },
        tabSize: 4,
        scrollBeyondLastLine: false,
        automaticLayout: true,
        padding: { top: 10 },
        renderLineHighlight: "line",
        smoothScrolling: true,
      }}
    />
  );
}
