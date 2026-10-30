import { Link } from "react-router-dom";
import type { ProblemRow } from "../api";
import { DiffText, FreqBar, pct, StatusIcon } from "./ui";

export default function ProblemTable({ rows, showFreq, linkSuffix = "" }: { rows: ProblemRow[]; showFreq: boolean; linkSuffix?: string }) {
  return (
    <div className="ptable" role="table" aria-label="Problems">
      <div className="prow head" role="row">
        <span role="columnheader">Status</span>
        <span role="columnheader">Title</span>
        <span role="columnheader">Difficulty</span>
        <span role="columnheader">Acceptance</span>
        <span role="columnheader">Topics</span>
        <span role="columnheader">{showFreq ? "Frequency" : ""}</span>
      </div>
      {rows.map((r) => (
        <div className="prow" role="row" key={r.slug}>
          <span role="cell"><StatusIcon status={r.status} /></span>
          <span role="cell" style={{ minWidth: 0, display: "flex", alignItems: "center", gap: 8 }}>
            <Link className="ttl" to={`/problems/${r.slug}${linkSuffix}`}>{r.id}. {r.title}</Link>
            {!r.has_tests && <span className="tag" title="Readable, but there are no tests to run">read-only</span>}
          </span>
          <span role="cell"><DiffText d={r.difficulty} /></span>
          <span role="cell" className="mono" style={{ fontSize: 12, color: "var(--fg2)" }}>{pct(r.acceptance)}</span>
          <span role="cell" style={{ display: "flex", gap: 4, overflow: "hidden" }}>
            {r.tags.slice(0, 2).map((t) => <span key={t} className="tag">{t}</span>)}
            {r.tags.length > 2 && <span className="muted" style={{ fontSize: 11.5 }}>+{r.tags.length - 2}</span>}
          </span>
          <span role="cell">{showFreq && <FreqBar value={r.frequency} />}</span>
        </div>
      ))}
      {rows.length === 0 && <div style={{ padding: 24, textAlign: "center" }} className="muted">No problems match these filters.</div>}
    </div>
  );
}
