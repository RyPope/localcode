import type { ImportStats } from "../api";

/** "12. Title", or just the title for repo-kept problems without a number. */
export function problemLabel(p: { id: number | null; title: string }): string {
  return p.id == null ? p.title : `${p.id}. ${p.title}`;
}

const count = (n: number, one: string, many = `${one}s`) => `${n.toLocaleString("en-US")} ${n === 1 ? one : many}`;

/** One phrase per non-empty part of an import's stats, for the Refresh content card. */
export function refreshSummary(s: ImportStats): string[] {
  const out: string[] = [];
  if (s.problems != null) out.push(count(s.problems, "problem"));
  if (s.companies != null) out.push(count(s.companies, "company", "companies"));
  const local = [
    s.local_problems ? count(s.local_problems, "local problem") : "",
    s.local_solutions ? count(s.local_solutions, "local solution") : "",
  ].filter(Boolean);
  if (local.length) out.push(local.join(", "));
  const kept = [
    s.kept_problems ? count(s.kept_problems, "problem") : "",
    s.kept_solutions ? count(s.kept_solutions, "solution") : "",
    s.kept_cases ? count(s.kept_cases, "test case") : "",
  ].filter(Boolean);
  if (kept.length) out.push(`kept ${kept.join(", ")} no longer upstream`);
  return out;
}
