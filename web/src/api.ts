export type Lang = "python" | "java" | "cpp" | "kotlin";
export type Difficulty = "Easy" | "Medium" | "Hard";
export type Status = "solved" | "attempted" | "todo";
export type Window = "30d" | "3m" | "6m" | "older" | "all";

export const LANG_LABEL: Record<Lang, string> = { python: "Python 3", java: "Java", cpp: "C++", kotlin: "Kotlin" };
export const WINDOW_LABEL: Record<Window, string> = {
  "30d": "30 days",
  "3m": "3 months",
  "6m": "6 months",
  older: "Older",
  all: "All time",
};

export interface ProblemRow {
  slug: string;
  id: number;
  title: string;
  difficulty: Difficulty;
  acceptance: number | null;
  tags: string[];
  frequency: number | null;
  status: Status;
  has_tests: boolean;
}
export interface ProblemList {
  total: number;
  items: ProblemRow[];
  counts: Record<"easy" | "medium" | "hard", [number, number]>;
}
export interface Param {
  name: string;
  type: string;
}
export interface ProblemDetail {
  slug: string;
  id: number;
  title: string;
  difficulty: Difficulty;
  tags: string[];
  acceptance: number | null;
  description_html: string;
  params: Param[];
  examples: unknown[][];
  has_tests: boolean;
  langs: Lang[];
  starters: Partial<Record<Lang, string>>;
  companies: { slug: string; name: string; frequency: number }[];
  status: Status;
  prev: string | null;
  next: string | null;
  test_count: number;
}
export interface Solution {
  title: string;
  explanation_md: string;
  code: Partial<Record<Lang, string>>;
  notes: Partial<Record<Lang, string>>;
}
export interface RunCase {
  args: unknown[];
  expected: unknown;
  actual: unknown;
  stdout: string;
  ok: boolean;
  error: string | null;
  ms: number | null;
}
export interface RunResult {
  verdict: string;
  compile_error: string | null;
  cases: RunCase[];
}
export interface Failing {
  args: unknown[];
  expected: unknown;
  actual: unknown;
  stdout: string;
  error: string | null;
}
export interface SubmitResult {
  verdict: string;
  passed: number;
  total: number;
  runtime_ms: number | null;
  memory_kb: number;
  failing: Failing | null;
  compile_error: string | null;
  submission_id: number;
}
export interface Submission {
  id: number;
  slug: string;
  lang: Lang;
  code: string;
  verdict: string;
  passed: number;
  total: number;
  runtime_ms: number | null;
  memory_kb: number;
  failing: Failing | null;
  created_at: string;
}
export interface Company {
  slug: string;
  name: string;
  count: number;
}
export interface CompanySummary {
  slug: string;
  name: string;
  window: Window;
  total: number;
  windows: Record<Window, number>;
  by_difficulty: Record<Difficulty, number>;
  top_topics: { name: string; count: number }[];
  solved: number;
  attempted: number;
  next_unsolved: { slug: string; id: number; title: string; difficulty: Difficulty }[];
  updated: string | null;
}
export interface Stats {
  since: string | null;
  totals: Record<"easy" | "medium" | "hard", [number, number]>;
  solved_by_week: { week: string; easy: number; medium: number; hard: number }[];
  by_topic: { name: string; solved: number; total: number }[];
  by_company: { slug: string; name: string; solved: number; total: number }[];
}
export interface AppStatus {
  imported: boolean;
  import: { running: boolean; step: string | null; done: number; total: number; log: string[]; error: string | null };
  meta: {
    imported_at?: string;
    stats?: { problems: number; with_tests: number; cases: number; companies: number };
    sources?: Record<string, string>;
  };
  toolchains: Partial<Record<Lang, string>> | null;
}

export class ApiError extends Error {}

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(path, { headers: { "Content-Type": "application/json" }, ...init });
  if (!r.ok) {
    let msg = `${r.status} ${r.statusText}`;
    try {
      msg = (await r.json()).detail ?? msg;
    } catch {
      /* not JSON */
    }
    throw new ApiError(msg);
  }
  return r.status === 204 ? (undefined as T) : r.json();
}

const qs = (o: Record<string, string | number | undefined>) =>
  new URLSearchParams(
    Object.entries(o)
      .filter(([, v]) => v !== undefined && v !== "")
      .map(([k, v]) => [k, String(v)]),
  ).toString();

export const api = {
  status: () => req<AppStatus>("/api/status"),
  startImport: () => req<{ started: boolean }>("/api/import", { method: "POST" }),
  problems: (p: Record<string, string | number | undefined>) => req<ProblemList>(`/api/problems?${qs(p)}`),
  tags: () => req<{ name: string; count: number }[]>("/api/tags"),
  problem: (slug: string) => req<ProblemDetail>(`/api/problems/${slug}`),
  solutions: (slug: string) => req<Solution[]>(`/api/problems/${slug}/solutions`),
  draft: (slug: string, lang: Lang) => req<{ code: string | null }>(`/api/drafts/${slug}/${lang}`),
  saveDraft: (slug: string, lang: Lang, code: string) =>
    req<void>(`/api/drafts/${slug}/${lang}`, { method: "PUT", body: JSON.stringify({ code }) }),
  run: (slug: string, lang: Lang, code: string, custom: string[]) =>
    req<RunResult>("/api/run", { method: "POST", body: JSON.stringify({ slug, lang, code, custom }) }),
  submit: (slug: string, lang: Lang, code: string) =>
    req<SubmitResult>("/api/submit", { method: "POST", body: JSON.stringify({ slug, lang, code }) }),
  submissions: (slug: string) => req<Submission[]>(`/api/submissions/${slug}`),
  companies: (q = "") => req<Company[]>(`/api/companies?${qs({ q })}`),
  company: (slug: string, window: Window) => req<CompanySummary>(`/api/companies/${slug}?${qs({ window })}`),
  stats: () => req<Stats>("/api/stats"),
};

/** `nums = [2,7], target = 9` — the same format the Run panel accepts for custom cases. */
export function formatArgs(params: Param[], args: unknown[]): string {
  return params.map((p, i) => `${p.name} = ${JSON.stringify(args[i])}`).join(", ");
}

export function fmtValue(v: unknown): string {
  return v === undefined ? "" : JSON.stringify(v);
}
