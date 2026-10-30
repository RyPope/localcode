import { useQuery } from "@tanstack/react-query";
import { ICONS } from "../lib/icons";
import { useState } from "react";
import { api, LANG_LABEL, type Lang } from "../api";
import styles from "./SubmissionsTab.module.css";
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
  if (!list.length) return <div className="empty">No submissions yet. They're stored locally on this machine.</div>;
  return (
    <div className="pane">
      <div className="row spread">
        <h2 className="title-2">Your submissions</h2>
        <span className="note">Stored locally</span>
      </div>
      <div className="ptable">
        <div className={`prow head ${styles.row}`}>
          <span>Status</span>
          <span>Language</span>
          <span>Passed</span>
          <span>Runtime</span>
          <span>Submitted</span>
        </div>
        {list.map((s) => (
          <button
            key={s.id}
            className={`prow ${styles.row} ${styles.item} ${cur?.id === s.id ? styles.selected : ""}`}
            onClick={() => setSel(s.id)}
          >
            <span className={s.verdict === "Accepted" ? styles.accepted : styles.rejected}>{s.verdict}</span>
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
          <div className="row tight">
            <span className="strong">{cur.verdict}</span>
            <span className="muted">
              {LANG_LABEL[cur.lang]} · {ago(cur.created_at)}
            </span>
            <div className="spacer" />
            <button className="btn" onClick={() => navigator.clipboard.writeText(cur.code)}>
              <Icon d={ICONS.copy} /> Copy
            </button>
            <button className="btn" onClick={() => onLoad(cur.lang, cur.code)}>
              Load into editor
            </button>
          </div>
          <pre className={`pre ${styles.code}`}>{cur.code}</pre>
        </>
      )}
    </div>
  );
}
