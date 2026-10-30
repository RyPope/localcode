import Editor from "@monaco-editor/react";
import { ICONS } from "../lib/icons";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { api, LANG_LABEL, type Lang } from "../api";
import "../monaco";
import { useTheme } from "../useTheme";
import { Icon, Markdown } from "./ui";

const MONACO_LANG: Record<Lang, string> = { python: "python", java: "java", cpp: "cpp", kotlin: "kotlin" };

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
  if (sols.isLoading)
    return (
      <div style={{ padding: 20 }} className="muted">
        Loading…
      </div>
    );
  if (!sols.data?.length)
    return (
      <div style={{ padding: 20 }} className="muted">
        No reference solution for this problem.
      </div>
    );
  const s = sols.data[Math.min(idx, sols.data.length - 1)];
  const langs = (Object.keys(LANG_LABEL) as Lang[]).filter((l) => s.code[l]);
  const shown = langs.includes(viewLang) ? viewLang : langs[0];
  const code = shown ? (s.code[shown] ?? "") : "";
  return (
    <div style={{ padding: "16px 20px", display: "flex", flexDirection: "column", gap: 14 }}>
      {sols.data.length > 1 && (
        <div className="seg" role="group" aria-label="Approach">
          {sols.data.map((x, i) => (
            <button key={i} className={i === idx ? "on" : ""} onClick={() => setIdx(i)}>
              {i + 1}. {x.title}
            </button>
          ))}
        </div>
      )}
      <div>
        <h2 style={{ margin: 0, fontSize: 16, fontWeight: 600 }}>{s.title}</h2>
        <span className="muted" style={{ fontSize: 12 }}>
          Reference solution · doocs/leetcode · CC BY-SA 4.0
        </span>
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
        <div className="seg" role="group" aria-label="Solution language">
          {langs.map((l) => (
            <button key={l} className={l === shown ? "on" : ""} onClick={() => setViewLang(l)}>
              {LANG_LABEL[l]}
            </button>
          ))}
        </div>
        <div style={{ flex: 1 }} />
        <button className="btn" onClick={() => navigator.clipboard.writeText(code)}>
          <Icon d={ICONS.copy} /> Copy
        </button>
        {shown && (
          <button className="btn" onClick={() => onOpen(shown, code)}>
            Open in editor
          </button>
        )}
      </div>
      {shown && s.notes[shown] && (
        <div className="muted" style={{ fontSize: 12 }}>
          {s.notes[shown]}
        </div>
      )}
      <div
        style={{
          border: "1px solid var(--line)",
          borderRadius: 8,
          overflow: "hidden",
          height: Math.min(560, 40 + code.split("\n").length * 19),
        }}
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
