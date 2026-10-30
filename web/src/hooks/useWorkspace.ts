import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useCallback, useEffect, useRef, useState } from "react";
import { api, type Lang, type ProblemDetail, type RunResult, type SubmitResult } from "../api";
import type { PanelTab } from "../components/TestPanel";
import { pref, setPref } from "../theme";

const AUTOSAVE_MS = 800;

export type SaveState = "saved" | "saving" | "dirty";

function pickLang(p: ProblemDetail): Lang {
  const available = p.langs.length ? p.langs : (Object.keys(p.starters) as Lang[]);
  const preferred = pref<Lang>("lang", "python");
  return available.includes(preferred) ? preferred : (available[0] ?? "python");
}

/** All editor/test state for one problem: language, per-language code with autosave, Run and Submit. */
export function useWorkspace(slug: string) {
  const qc = useQueryClient();
  const problem = useQuery({ queryKey: ["problem", slug], queryFn: () => api.problem(slug) });
  const [lang, setLangState] = useState<Lang>("python");
  const [code, setCodeState] = useState<string>("");
  const [save, setSave] = useState<SaveState>("saved");
  const [custom, setCustom] = useState<string[]>([]);
  const [tab, setTab] = useState<PanelTab>("cases");
  const [runResult, setRunResult] = useState<RunResult | null>(null);
  const [submission, setSubmission] = useState<SubmitResult | null>(null);
  const timer = useRef<number>();
  const pending = useRef<{ lang: Lang; code: string } | null>(null);

  const flush = useCallback(() => {
    window.clearTimeout(timer.current);
    const p = pending.current;
    if (!p) return;
    pending.current = null;
    setSave("saving");
    api.saveDraft(slug, p.lang, p.code).then(() => {
      setSave(pending.current ? "dirty" : "saved");
      qc.invalidateQueries({ queryKey: ["problems"] });
    });
  }, [qc, slug]);

  const load = useCallback(
    async (p: ProblemDetail, l: Lang) => {
      const draft = await api.draft(slug, l);
      setCodeState(draft.code ?? p.starters[l] ?? "");
      setSave("saved");
    },
    [slug],
  );

  // Reset per-problem state when the problem changes.
  // Reset only when a different problem loads; refetches of the same problem (after Submit
  // updates its status) must not wipe the editor or results.
  const initialized = useRef<string | null>(null);
  useEffect(() => {
    if (!problem.data || initialized.current === problem.data.slug) return;
    initialized.current = problem.data.slug;
    const l = pickLang(problem.data);
    setLangState(l);
    setCustom([]);
    setRunResult(null);
    setSubmission(null);
    setTab("cases");
    void load(problem.data, l);
  }, [problem.data, load]);

  useEffect(() => () => flush(), [flush]);

  const setCode = useCallback(
    (value: string) => {
      setCodeState(value);
      setSave("dirty");
      pending.current = { lang, code: value };
      window.clearTimeout(timer.current);
      timer.current = window.setTimeout(flush, AUTOSAVE_MS);
    },
    [flush, lang],
  );

  const setLang = useCallback(
    (l: Lang) => {
      flush();
      setLangState(l);
      setPref("lang", l);
      if (problem.data) void load(problem.data, l);
    },
    [flush, load, problem.data],
  );

  /** Put code into the editor for a language (from a reference solution or past submission). */
  const loadCode = useCallback(
    (l: Lang, value: string) => {
      flush();
      setLangState(l);
      setCodeState(value);
      pending.current = { lang: l, code: value };
      flush();
    },
    [flush],
  );

  const resetToStarter = useCallback(() => {
    if (problem.data) setCode(problem.data.starters[lang] ?? "");
  }, [lang, problem.data, setCode]);

  const run = useMutation({
    mutationFn: () => {
      flush();
      return api.run(slug, lang, code, custom);
    },
    onMutate: () => setTab("result"),
    onSuccess: (r) => setRunResult(r),
  });

  const submit = useMutation({
    mutationFn: () => {
      flush();
      return api.submit(slug, lang, code);
    },
    onMutate: () => setTab("submission"),
    onSuccess: (r) => {
      setSubmission(r);
      setTab("submission");
      for (const key of [["submissions", slug], ["problem", slug], ["problems"], ["company"], ["stats"]]) {
        qc.invalidateQueries({ queryKey: key });
      }
    },
  });

  const error = (run.error ?? submit.error) as Error | null;
  return {
    problem,
    lang,
    setLang,
    code,
    setCode,
    save,
    loadCode,
    resetToStarter,
    custom,
    setCustom,
    tab,
    setTab,
    runResult,
    submission,
    run: () => run.mutate(),
    submit: () => submit.mutate(),
    busy: run.isPending || submit.isPending,
    error: error?.message ?? null,
  };
}
