import { LANG_LABEL, type Lang } from "../api";
import type { SaveState } from "../hooks/useWorkspace";
import { ICONS } from "../lib/icons";
import styles from "./EditorToolbar.module.css";
import { Icon } from "./ui";

const SAVE_LABEL: Record<SaveState, string> = {
  saved: "Saved locally",
  saving: "Saving…",
  dirty: "Unsaved",
  error: "Couldn't save — retrying",
};

export function EditorToolbar(props: {
  langs: Lang[];
  lang: Lang;
  onLang: (lang: Lang) => void;
  onReset: () => void;
  fontSize: number;
  onFontSize: (delta: number) => void;
  save: SaveState;
  canRun: boolean;
  onRun: () => void;
  onSubmit: () => void;
}) {
  return (
    <div className={`tabs ${styles.toolbar}`}>
      <label className="sr" htmlFor="lang">
        Language
      </label>
      <select id="lang" className="btn" value={props.lang} onChange={(e) => props.onLang(e.target.value as Lang)}>
        {props.langs.map((l) => (
          <option key={l} value={l}>
            {LANG_LABEL[l]}
          </option>
        ))}
      </select>
      <button className="btn ghost" onClick={props.onReset} title="Reset to starter code">
        <Icon d={ICONS.reset} /> Reset
      </button>
      <button className="btn ghost ibtn" aria-label="Smaller font" onClick={() => props.onFontSize(-1)}>
        A−
      </button>
      <span className="mono muted text-xs">{props.fontSize}px</span>
      <button className="btn ghost ibtn" aria-label="Larger font" onClick={() => props.onFontSize(1)}>
        A+
      </button>
      <span className={props.save === "error" ? "note bad" : "note"}>{SAVE_LABEL[props.save]}</span>
      <div className="spacer" />
      <button className="btn" disabled={!props.canRun} onClick={props.onRun} title="Run (⌘↵)">
        <Icon d={ICONS.play} /> Run <span className="kbd">⌘↵</span>
      </button>
      <button className="btn primary" disabled={!props.canRun} onClick={props.onSubmit} title="Submit (⌘⇧↵)">
        <Icon d={ICONS.upload} /> Submit
      </button>
    </div>
  );
}

export function EditorStatusBar({ toolchain, warning }: { toolchain: string; warning: string | null }) {
  return (
    <div className={`mono ${styles.statusBar}`}>
      <span>{toolchain}</span>
      <span>sandboxed · no network</span>
      {warning && <span className="warn">{warning}</span>}
    </div>
  );
}
