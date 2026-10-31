import Editor from "@monaco-editor/react";
import { ICONS } from "../lib/icons";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { api, LANG_LABEL, type Lang } from "../api";
import { MONACO_LANG } from "../monaco";
import { useTheme } from "../useTheme";
import { Icon, Markdown, Segmented } from "./ui";

const LINE_HEIGHT = 19;
const MAX_CODE_HEIGHT = 560;

export default function SolutionsTab({
  slug,
  lang,
  onOpen,
}: {
  slug: string;
  lang: Lang;
  onOpen: (lang: Lang, code: string) => void;
}) {
  const sols = useQuery({ queryKey: ["solutions", slug], queryFn: () => api.solutions(slug) });
  const [idx, setIdx] = useState(0);
  const [viewLang, setViewLang] = useState<Lang>(lang);
  const theme = useTheme();
  if (sols.isLoading) return <div className="empty">Loading…</div>;
  if (!sols.data?.length) return <div className="empty">No reference solution for this problem.</div>;
  const s = sols.data[Math.min(idx, sols.data.length - 1)];
  const langs = (Object.keys(LANG_LABEL) as Lang[]).filter((l) => s.code[l]);
  const shown = langs.includes(viewLang) ? viewLang : langs[0];
  const code = shown ? (s.code[shown] ?? "") : "";
  return (
    <div className="pane">
      {sols.data.length > 1 && (
        <Segmented
          label="Approach"
          value={String(idx)}
          onChange={(v) => setIdx(Number(v))}
          options={sols.data.map((x, i) => ({ value: String(i), label: `${i + 1}. ${x.title}` }))}
        />
      )}
      <div>
        <h2 className="title-2">{s.title}</h2>
        <span className="note">
          {s.local
            ? "Local solution · from this repo's content/ folder"
            : "Reference solution · doocs/leetcode · CC BY-SA 4.0"}
        </span>
      </div>
      <div className="row tight">
        {shown && (
          <Segmented
            label="Solution language"
            value={shown}
            onChange={setViewLang}
            options={langs.map((l) => ({ value: l, label: LANG_LABEL[l] }))}
          />
        )}
        <div className="spacer" />
        <button className="btn" onClick={() => navigator.clipboard.writeText(code)}>
          <Icon d={ICONS.copy} /> Copy
        </button>
        {shown && (
          <button className="btn" onClick={() => onOpen(shown, code)}>
            Open in editor
          </button>
        )}
      </div>
      {shown && s.notes[shown] && <div className="note">{s.notes[shown]}</div>}
      <div
        className="code-frame"
        style={{ height: Math.min(MAX_CODE_HEIGHT, 40 + code.split("\n").length * LINE_HEIGHT) }}
      >
        <Editor
          value={code}
          language={shown ? MONACO_LANG[shown] : "plaintext"}
          theme={theme === "light" ? "localcode-light" : "localcode-dark"}
          options={{
            readOnly: true,
            minimap: { enabled: false },
            fontSize: 13,
            fontFamily: "Geist Mono, monospace",
            scrollBeyondLastLine: false,
            lineNumbers: "on",
            renderLineHighlight: "none",
          }}
        />
      </div>
      <h3 className="lbl">Explanation</h3>
      <Markdown src={s.explanation_md} />
    </div>
  );
}
