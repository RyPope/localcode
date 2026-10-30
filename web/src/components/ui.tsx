import DOMPurify from "dompurify";
import { useMemo, type ReactNode } from "react";
import type { Difficulty, Status, Window } from "../api";
import { WINDOW_LABEL } from "../api";
import { ICONS } from "../lib/icons";
import { renderMarkdown } from "../lib/markdown";

export function Icon({ d, size = 14, stroke = 2 }: { d: string | string[]; size?: number; stroke?: number }) {
  return (
    <svg
      aria-hidden="true"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={stroke}
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      {(Array.isArray(d) ? d : [d]).map((p) => (
        <path key={p} d={p} />
      ))}
    </svg>
  );
}

export function StatusIcon({ status }: { status: Status }) {
  if (status === "solved")
    return (
      <span className="ok" title="Solved" aria-label="Solved">
        <Icon d={ICONS.check} stroke={2.6} />
      </span>
    );
  if (status === "attempted") return <span title="Attempted" aria-label="Attempted" className="dot attempted" />;
  return <span aria-label="Not started" />;
}

export function DiffText({ d }: { d: Difficulty }) {
  return <span className={`diff ${d}`}>{d}</span>;
}

const BADGE_COLORS = [
  ["#2B3A5C", "#C9D6FF"],
  ["#4A3A1E", "#F5D9A6"],
  ["#1F3E4A", "#A9E3F5"],
  ["#2E3B2A", "#C7E8B8"],
  ["#45283A", "#F2BFDC"],
  ["#363A40", "#D9DDE3"],
  ["#3A2E4D", "#D8C8F5"],
  ["#4A2A2A", "#F5C2BC"],
];

export function CompanyBadge({ name, size = 20 }: { name: string; size?: number }) {
  let h = 0;
  for (const ch of name) h = (h * 31 + ch.charCodeAt(0)) >>> 0;
  const [bg, fg] = BADGE_COLORS[h % BADGE_COLORS.length];
  const initials = name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0])
    .join("")
    .toUpperCase();
  return (
    <span
      className="mono-badge"
      aria-hidden="true"
      style={{ background: bg, color: fg, width: size, height: size, fontSize: size * 0.5 }}
    >
      {initials}
    </span>
  );
}

export interface SegmentOption<T extends string> {
  value: T;
  label: ReactNode;
}

/** Single-choice segmented control. */
export function Segmented<T extends string>({
  label,
  options,
  value,
  onChange,
}: {
  label: string;
  options: readonly SegmentOption<T>[];
  value: T;
  onChange: (value: T) => void;
}) {
  return (
    <div className="seg" role="group" aria-label={label}>
      {options.map((o) => (
        <button
          key={o.value}
          className={o.value === value ? "on" : ""}
          aria-pressed={o.value === value}
          onClick={() => onChange(o.value)}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}

export function WindowToggle({
  value,
  onChange,
  counts,
  options = ["30d", "3m", "6m", "all"],
}: {
  value: Window;
  onChange: (w: Window) => void;
  counts?: Partial<Record<string, number>>;
  options?: Window[];
}) {
  return (
    <Segmented
      label="Time window"
      value={value}
      onChange={onChange}
      options={options.map((w) => ({
        value: w,
        label: (
          <>
            {WINDOW_LABEL[w]}
            {counts?.[w] !== undefined && <span className="seg-count">{counts[w]}</span>}
          </>
        ),
      }))}
    />
  );
}

export function FreqBar({ value }: { value: number | null }) {
  if (value == null) return <span className="muted">—</span>;
  return (
    <div className="freq" title={`Frequency ${value.toFixed(1)}`}>
      <div className="bar">
        <span style={{ width: `${Math.max(2, Math.min(100, value))}%` }} />
      </div>
      <span className="mono freq-value">{value.toFixed(0)}</span>
    </div>
  );
}

/** Sanitised HTML from imported content (problem statements). */
export function Html({ html, className = "prose" }: { html: string; className?: string }) {
  const clean = useMemo(() => DOMPurify.sanitize(html, { ADD_ATTR: ["target"] }), [html]);
  return <div className={className} dangerouslySetInnerHTML={{ __html: clean }} />;
}

/** Markdown with $math$ (KaTeX), for reference-solution explanations. */
export function Markdown({ src }: { src: string }) {
  const clean = useMemo(() => DOMPurify.sanitize(renderMarkdown(src)), [src]);
  return <div className="prose" dangerouslySetInnerHTML={{ __html: clean }} />;
}

export function Pager({
  page,
  total,
  size,
  onPage,
}: {
  page: number;
  total: number;
  size: number;
  onPage: (p: number) => void;
}) {
  const last = Math.max(1, Math.ceil(total / size));
  const from = total === 0 ? 0 : (page - 1) * size + 1;
  return (
    <div className="pager">
      <span className="note">
        Showing {from.toLocaleString()}–{Math.min(page * size, total).toLocaleString()} of {total.toLocaleString()}
      </span>
      <div className="spacer" />
      <button className="btn" disabled={page <= 1} onClick={() => onPage(page - 1)}>
        Previous
      </button>
      <button className="btn" disabled={page >= last} onClick={() => onPage(page + 1)}>
        Next
      </button>
    </div>
  );
}
