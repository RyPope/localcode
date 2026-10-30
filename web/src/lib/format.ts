/** Acceptance rate (0–1) as a percentage, or an em dash when unknown. */
export function pct(v: number | null | undefined) {
  return v == null ? "—" : `${(v * 100).toFixed(1)}%`;
}
