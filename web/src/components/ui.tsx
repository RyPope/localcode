import DOMPurify from "dompurify";
import katex from "katex";
import { marked } from "marked";
import { useMemo } from "react";
import type { Difficulty, Status, Window } from "../api";
import { WINDOW_LABEL } from "../api";

export function Icon({ d, size = 14, stroke = 2 }: { d: string | string[]; size?: number; stroke?: number }) {
  return (
    <svg aria-hidden="true" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor"
      strokeWidth={stroke} strokeLinecap="round" strokeLinejoin="round">
      {(Array.isArray(d) ? d : [d]).map((p) => <path key={p} d={p} />)}
    </svg>
  );
}

export const ICONS = {
  logo: ["M8 7l-5 5 5 5", "M16 7l5 5-5 5"],
  search: ["M11 18a7 7 0 1 0 0-14 7 7 0 0 0 0 14z", "M20 20l-3.5-3.5"],
  sun: ["M12 16a4 4 0 1 0 0-8 4 4 0 0 0 0 8z", "M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"],
  check: "M5 12l5 5 9-9",
  play: "M7 5l12 7-12 7z",
  upload: ["M12 17V5", "M7 10l5-5 5 5", "M5 21h14"],
  reset: ["M3 12a9 9 0 1 0 3-6.7L3 8", "M3 3v5h5"],
  copy: ["M9 9h11v11H9z", "M5 15H4V4h11v1"],
  download: ["M12 3v12", "M7 10l5 5 5-5", "M5 21h14"],
  refresh: ["M21 12a9 9 0 1 1-3-6.7L21 8", "M21 3v5h-5"],
  left: "M15 18l-6-6 6-6",
  right: "M9 18l6-6-6-6",
  plus: "M12 5v14M5 12h14",
  x: "M6 6l12 12M18 6L6 18",
};

export function StatusIcon({ status }: { status: Status }) {
  if (status === "solved")
    return <span className="ok" title="Solved" aria-label="Solved"><Icon d={ICONS.check} stroke={2.6} /></span>;
  if (status === "attempted")
    return <span title="Attempted" aria-label="Attempted" className="dot" style={{ background: "var(--med)" }} />;
  return <span aria-label="Not started" />;
}

export function DiffText({ d }: { d: Difficulty }) {
  return <span className={`diff ${d}`}>{d}</span>;
}

export function pct(v: number | null | undefined) {
  return v == null ? "—" : `${(v * 100).toFixed(1)}%`;
}

const BADGE_COLORS = [
  ["#2B3A5C", "#C9D6FF"], ["#4A3A1E", "#F5D9A6"], ["#1F3E4A", "#A9E3F5"], ["#2E3B2A", "#C7E8B8"],
  ["#45283A", "#F2BFDC"], ["#363A40", "#D9DDE3"], ["#3A2E4D", "#D8C8F5"], ["#4A2A2A", "#F5C2BC"],
];

export function CompanyBadge({ name, size = 20 }: { name: string; size?: number }) {
  let h = 0;
  for (const ch of name) h = (h * 31 + ch.charCodeAt(0)) >>> 0;
  const [bg, fg] = BADGE_COLORS[h % BADGE_COLORS.length];
  const initials = name.split(/\s+/).filter(Boolean).slice(0, 2).map((w) => w[0]).join("").toUpperCase();
  return (
    <span className="mono-badge" aria-hidden="true"
      style={{ background: bg, color: fg, width: size, height: size, fontSize: size * 0.5 }}>
      {initials}
    </span>
  );
}

export function WindowToggle({ value, onChange, counts, options = ["30d", "3m", "6m", "all"] }: {
  value: Window; onChange: (w: Window) => void; counts?: Partial<Record<Window, number>>; options?: Window[];
}) {
  return (
    <div className="seg" role="group" aria-label="Time window">
      {options.map((w) => (
        <button key={w} className={w === value ? "on" : ""} aria-pressed={w === value} onClick={() => onChange(w)}>
          {WINDOW_LABEL[w]}
          {counts && counts[w] !== undefined && <span className="muted" style={{ marginLeft: 6 }}>{counts[w]}</span>}
        </button>
      ))}
    </div>
  );
}

export function FreqBar({ value }: { value: number | null }) {
  if (value == null) return <span className="muted">—</span>;
  return (
    <div className="freq" title={`Frequency ${value.toFixed(1)}`}>
      <div className="bar"><span style={{ width: `${Math.max(2, Math.min(100, value))}%` }} /></div>
      <span className="mono muted" style={{ fontSize: 11.5, width: 32, textAlign: "right" }}>{value.toFixed(0)}</span>
    </div>
  );
}

/** Sanitised HTML from imported content (problem statements). */
export function Html({ html, className = "prose" }: { html: string; className?: string }) {
  const clean = useMemo(() => DOMPurify.sanitize(html, { ADD_ATTR: ["target"] }), [html]);
  return <div className={className} dangerouslySetInnerHTML={{ __html: clean }} />;
}

function renderMath(src: string): string {
  const parts: string[] = [];
  const stash = (html: string) => `\u0000${parts.push(html) - 1}\u0000`;
  const tex = (s: string, display: boolean) => katex.renderToString(s, { throwOnError: false, displayMode: display });
  const withMath = src
    .replace(/\$\$([\s\S]+?)\$\$/g, (_, s) => stash(tex(s, true)))
    .replace(/\$([^$\n]+?)\$/g, (_, s) => stash(tex(s, false)));
  const html = marked.parse(withMath, { async: false }) as string;
  return html.replace(/\u0000(\d+)\u0000/g, (_, i) => parts[Number(i)]);
}

/** Markdown with $math$ (KaTeX), for reference-solution explanations. */
export function Markdown({ src }: { src: string }) {
  const clean = useMemo(() => DOMPurify.sanitize(renderMath(src)), [src]);
  return <div className="prose" dangerouslySetInnerHTML={{ __html: clean }} />;
}

export function Pager({ page, total, size, onPage }: { page: number; total: number; size: number; onPage: (p: number) => void }) {
  const last = Math.max(1, Math.ceil(total / size));
  const from = total === 0 ? 0 : (page - 1) * size + 1;
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "10px 4px" }}>
      <span className="muted" style={{ fontSize: 12 }}>
        Showing {from.toLocaleString()}–{Math.min(page * size, total).toLocaleString()} of {total.toLocaleString()}
      </span>
      <div style={{ flex: 1 }} />
      <button className="btn" disabled={page <= 1} onClick={() => onPage(page - 1)}>Previous</button>
      <button className="btn" disabled={page >= last} onClick={() => onPage(page + 1)}>Next</button>
    </div>
  );
}
