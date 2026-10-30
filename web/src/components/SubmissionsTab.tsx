import { useQuery } from "@tanstack/react-query";
import { ICONS } from "../lib/icons";
import { useState } from "react";
import { api, LANG_LABEL, type Lang } from "../api";
import { Icon } from "./ui";

function ago(iso: string) {
  const s = (Date.now() - new Date(iso).getTime()) / 1000;
  if (s < 60) return "just now";
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  if (s < 86400) return `${Math.floor(s / 3600)}h ago`;
  return new Date(iso).toLocaleDateString();
}

export default function SubmissionsTab({ slug, onLoad }: { slug: string; onLoad: (lang: Lang, code: string) => void }) {
  const subs = useQuery({ queryKey: ["submissions", slug], queryFn: () => api.submissions(slug) });
  const [sel, setSel] = useState<number | null>(null);
  const list = subs.data ?? [];
  const cur = list.find((s) => s.id === sel) ?? list[0];
  if (!list.length)
    return (
      <div style={{ padding: 20 }} className="muted">
        No submissions yet. They're stored locally on this machine.
      </div>
    );
  return (
    <div style={{ padding: "16px 20px", display: "flex", flexDirection: "column", gap: 12 }}>
      <div style={{ display: "flex", justifyContent: "space-between" }}>
        <h2 style={{ margin: 0, fontSize: 15, fontWeight: 600 }}>Your submissions</h2>
        <span className="muted" style={{ fontSize: 12 }}>
          Stored locally
        </span>
      </div>
      <div className="ptable">
        <div className="prow head" style={{ gridTemplateColumns: "1.4fr 1fr 0.8fr 0.9fr 1fr", minWidth: 0 }}>
          <span>Status</span>
          <span>Language</span>
          <span>Passed</span>
          <span>Runtime</span>
          <span>Submitted</span>
        </div>
        {list.map((s) => (
          <button
            key={s.id}
            className="prow"
            onClick={() => setSel(s.id)}
            style={{
              gridTemplateColumns: "1.4fr 1fr 0.8fr 0.9fr 1fr",
              minWidth: 0,
              width: "100%",
              border: 0,
              borderBottom: "1px solid var(--line)",
              background: cur?.id === s.id ? "var(--sel)" : "transparent",
              textAlign: "left",
            }}
          >
            <span style={{ color: s.verdict === "Accepted" ? "var(--easy)" : "var(--hard)", fontWeight: 500 }}>
              {s.verdict}
            </span>
            <span>{LANG_LABEL[s.lang]}</span>
            <span className="mono">
              {s.passed}/{s.total}
            </span>
            <span className="mono">{s.runtime_ms != null ? `${s.runtime_ms.toFixed(0)} ms` : "—"}</span>
            <span className="muted">{ago(s.created_at)}</span>
          </button>
        ))}
      </div>
      {cur && (
        <>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ fontWeight: 600 }}>{cur.verdict}</span>
            <span className="muted">
              {LANG_LABEL[cur.lang]} · {ago(cur.created_at)}
            </span>
            <div style={{ flex: 1 }} />
            <button className="btn" onClick={() => navigator.clipboard.writeText(cur.code)}>
              <Icon d={ICONS.copy} /> Copy
            </button>
            <button className="btn" onClick={() => onLoad(cur.lang, cur.code)}>
              Load into editor
            </button>
          </div>
          <pre className="pre" style={{ maxHeight: 360, overflow: "auto" }}>
            {cur.code}
          </pre>
        </>
      )}
    </div>
  );
}
