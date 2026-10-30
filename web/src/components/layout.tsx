import type { ReactNode } from "react";
import { ICONS } from "../lib/icons";
import { Icon } from "./ui";

/** Page title row: title, optional muted subtitle, and right-aligned actions. */
export function PageHeader({
  title,
  subtitle,
  children,
}: {
  title: ReactNode;
  subtitle?: ReactNode;
  children?: ReactNode;
}) {
  return (
    <div className="row">
      <h1 className="title-1">{title}</h1>
      {subtitle && <span className="note text-sm">{subtitle}</span>}
      <div className="spacer" />
      {children}
    </div>
  );
}

/** Card heading with an optional note on the right. */
export function CardHeader({ title, note, children }: { title: ReactNode; note?: ReactNode; children?: ReactNode }) {
  return (
    <div className="row spread">
      <h2 className="title-3">{title}</h2>
      {note && <span className="note">{note}</span>}
      {children}
    </div>
  );
}

/** "12 / 340" with the denominator de-emphasised. */
export function Stat({ value, of }: { value: number; of: number }) {
  return (
    <div className="stat">
      {value.toLocaleString()} <span className="stat-of">/ {of.toLocaleString()}</span>
    </div>
  );
}

/** Horizontal progress bar; `ratio` is clamped to 0–1. */
export function Meter({ ratio, color, label }: { ratio: number; color?: string; label?: string }) {
  const pct = Math.max(0, Math.min(1, Number.isFinite(ratio) ? ratio : 0)) * 100;
  return (
    <div className="bar" role={label ? "img" : undefined} aria-label={label}>
      <span style={{ width: `${pct}%`, background: color }} />
    </div>
  );
}

/** Text input with a search icon and an accessible (visually hidden) label. */
export function SearchInput({
  id,
  label,
  value,
  defaultValue,
  onChange,
  placeholder,
  autoFocus,
  width,
  inputRef,
  trailing,
}: {
  id: string;
  label: string;
  value?: string;
  defaultValue?: string;
  onChange: (value: string) => void;
  placeholder?: string;
  autoFocus?: boolean;
  width?: number;
  inputRef?: React.Ref<HTMLInputElement>;
  trailing?: ReactNode;
}) {
  return (
    <div className="search" style={width ? { width } : undefined}>
      <label className="sr" htmlFor={id}>
        {label}
      </label>
      <span className="search-icon">
        <Icon d={ICONS.search} />
      </span>
      <input
        id={id}
        ref={inputRef}
        className="inp icon"
        placeholder={placeholder ?? label}
        value={value}
        defaultValue={defaultValue}
        onChange={(e) => onChange(e.target.value)}
        autoFocus={autoFocus}
        autoComplete="off"
      />
      {trailing}
    </div>
  );
}
