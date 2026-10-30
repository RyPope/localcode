import { Link } from "react-router-dom";
import { pct } from "../lib/format";
import type { ProblemRow } from "../api";
import { DiffText, FreqBar, StatusIcon } from "./ui";

export default function ProblemTable({
  rows,
  showFreq,
  linkSuffix = "",
}: {
  rows: ProblemRow[];
  showFreq: boolean;
  linkSuffix?: string;
}) {
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
          <span role="cell">
            <StatusIcon status={r.status} />
          </span>
          <span role="cell" className="titleCell">
            <Link className="ttl" to={`/problems/${r.slug}${linkSuffix}`}>
              {r.id}. {r.title}
            </Link>
            {!r.has_tests && (
              <span className="tag" title="Readable, but there are no tests to run">
                read-only
              </span>
            )}
          </span>
          <span role="cell">
            <DiffText d={r.difficulty} />
          </span>
          <span role="cell" className="accCell">
            {pct(r.acceptance)}
          </span>
          <span role="cell" className="tagsCell">
            {r.tags.slice(0, 2).map((t) => (
              <span key={t} className="tag">
                {t}
              </span>
            ))}
            {r.tags.length > 2 && <span className="muted text-xs">+{r.tags.length - 2}</span>}
          </span>
          <span role="cell">{showFreq && <FreqBar value={r.frequency} />}</span>
        </div>
      ))}
      {rows.length === 0 && <div className="empty">No problems match these filters.</div>}
    </div>
  );
}
