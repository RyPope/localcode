import type { components, operations } from "./generated/api";

// Wire types are generated from the backend's OpenAPI document (`make api-types`); never edit them by hand.
type Schemas = components["schemas"];
export type ProblemRow = Schemas["ProblemRow"];
export type ProblemList = Schemas["ProblemList"];
export type Param = Schemas["Param"];
export type ProblemDetail = Schemas["ProblemDetail"];
export type Solution = Schemas["Solution"];
export type RunCase = Schemas["RunCase"];
export type RunResult = Schemas["RunResult"];
export type FailingCase = Schemas["FailingCase"];
export type SubmitResult = Schemas["SubmitResult"];
export type Submission = Schemas["Submission"];
export type Company = Schemas["Company"];
export type CompanySummary = Schemas["CompanySummary"];
export type Stats = Schemas["Stats"];
export type AppStatus = Schemas["AppStatus"];
export type ImportStats = Schemas["ImportStats"];
export type Tag = Schemas["Tag"];
export type ProblemQuery = NonNullable<operations["list_problems_api_problems_get"]["parameters"]["query"]>;

export type Lang = Schemas["SubmitRequest"]["lang"];
export type Difficulty = ProblemRow["difficulty"];
export type Status = ProblemRow["status"];
export type Window = CompanySummary["window"];

export const LANG_LABEL: Record<Lang, string> = { python: "Python 3", java: "Java", cpp: "C++", kotlin: "Kotlin" };
export const WINDOW_LABEL: Record<Window, string> = {
  "30d": "30 days",
  "3m": "3 months",
  "6m": "6 months",
  older: "Older",
  all: "All time",
};

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(path, { headers: { "Content-Type": "application/json" }, ...init });
  if (!r.ok) {
    let msg = `${r.status} ${r.statusText}`;
    try {
      msg = (await r.json()).detail ?? msg;
    } catch {
      /* not JSON */
    }
    throw new ApiError(msg, r.status);
  }
  return r.status === 204 ? (undefined as T) : r.json();
}

const qs = (o: Record<string, string | number | undefined>): string =>
  new URLSearchParams(
    Object.entries(o)
      .filter(([, v]) => v !== undefined && v !== "")
      .map(([k, v]) => [k, String(v)]),
  ).toString();

export const api = {
  status: () => req<AppStatus>("/api/status"),
  startImport: () => req<Schemas["ImportStarted"]>("/api/import", { method: "POST" }),
  problems: (query: ProblemQuery) => req<ProblemList>(`/api/problems?${qs(query)}`),
  tags: () => req<Tag[]>("/api/tags"),
  problem: (slug: string) => req<ProblemDetail>(`/api/problems/${slug}`),
  solutions: (slug: string) => req<Solution[]>(`/api/problems/${slug}/solutions`),
  draft: (slug: string, lang: Lang) => req<Schemas["Draft"]>(`/api/drafts/${slug}/${lang}`),
  saveDraft: (slug: string, lang: Lang, code: string, opts?: { keepalive?: boolean }) =>
    req<void>(`/api/drafts/${slug}/${lang}`, {
      method: "PUT",
      body: JSON.stringify({ code }),
      keepalive: opts?.keepalive,
    }),
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
