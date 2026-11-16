import Editor, { type OnMount } from "@monaco-editor/react";
import { initVimMode } from "monaco-vim";
import { useEffect, useRef, useState } from "react";
import type { Lang } from "../api";
import { MONACO_LANG, monaco } from "../monaco";
import { useTheme } from "../useTheme";
import styles from "./CodeEditor.module.css";

type MonacoEditor = Parameters<OnMount>[0];

export default function CodeEditor({
  lang,
  value,
  onChange,
  fontSize,
  onRun,
  onSubmit,
  vim,
}: {
  lang: Lang;
  value: string;
  onChange: (v: string) => void;
  fontSize: number;
  onRun: () => void;
  onSubmit: () => void;
  vim: boolean;
}) {
  const theme = useTheme();
  // Monaco registers commands once; keep the latest callbacks in refs.
  const actions = useRef({ onRun, onSubmit });
  useEffect(() => {
    actions.current = { onRun, onSubmit };
  }, [onRun, onSubmit]);

  const [editor, setEditor] = useState<MonacoEditor | null>(null);
  const vimStatus = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!vim || !editor || !vimStatus.current) return;
    const mode = initVimMode(editor, vimStatus.current);
    return () => mode.dispose();
  }, [vim, editor]);

  const onMount: OnMount = (editor) => {
    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, () => actions.current.onRun());
    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyMod.Shift | monaco.KeyCode.Enter, () =>
      actions.current.onSubmit(),
    );
    editor.focus();
    setEditor(editor);
  };

  return (
    <div className={styles.wrap}>
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
      {vim && <div ref={vimStatus} className={`mono ${styles.vimStatus}`} aria-live="polite" />}
    </div>
  );
}
