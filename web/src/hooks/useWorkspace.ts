import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useCallback, useEffect, useRef, useState } from "react";
import { api, type Lang, type ProblemDetail, type RunResult, type SubmitResult } from "../api";
import type { PanelTab } from "../components/TestPanel";
import { DraftSaver, type SaveState } from "../lib/draftSaver";
import { pref, setPref } from "../theme";

const AUTOSAVE_MS = 800;
const RETRY_MS = 3000;

export type { SaveState };

function pickLang(p: ProblemDetail): Lang {
  const available = p.langs.length ? p.langs : (Object.keys(p.starters) as Lang[]);
  const preferred = pref<Lang>("lang", "python");
  return available.includes(preferred) ? preferred : (available[0] ?? "python");
}

/**
 * All editor/test state for one problem: language, per-language code with autosave, Run and Submit.
 * Mount one instance per problem (the route keys the page by slug) so state never crosses problems.
 */
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

  const saver = useRef<DraftSaver | undefined>(undefined);
  saver.current ??= new DraftSaver({
    save: async (l, c, opts) => {
      await api.saveDraft(slug, l as Lang, c, opts);
      qc.invalidateQueries({ queryKey: ["problems"] });
    },
    onState: setSave,
    delayMs: AUTOSAVE_MS,
    retryMs: RETRY_MS,
  });

  useEffect(() => {
    const s = saver.current!;
    const onHide = () => s.flushOnExit();
    window.addEventListener("pagehide", onHide);
    return () => {
      window.removeEventListener("pagehide", onHide);
      void s.flush(); // leaving the problem inside the app
      s.dispose();
    };
  }, []);

  // Only the most recent draft request may update the editor (fast language switches race).
  const loadSeq = useRef(0);
  const load = useCallback(
    async (p: ProblemDetail, l: Lang) => {
      const seq = ++loadSeq.current;
      const draft = await api.draft(slug, l);
      if (seq !== loadSeq.current) return;
      setCodeState(draft.code ?? p.starters[l] ?? "");
      setSave("saved");
    },
    [slug],
  );

  // Initialise once per mount; later refetches of this problem (e.g. after Submit) keep the editor as is.
  const initialized = useRef(false);
  useEffect(() => {
    if (!problem.data || initialized.current) return;
    initialized.current = true;
    const l = pickLang(problem.data);
    setLangState(l);
    void load(problem.data, l);
  }, [problem.data, load]);

  const setCode = useCallback(
    (value: string) => {
      setCodeState(value);
      saver.current!.schedule(lang, value);
    },
    [lang],
  );

  const setLang = useCallback(
    (l: Lang) => {
      void saver.current!.flush();
      setLangState(l);
      setPref("lang", l);
      if (problem.data) void load(problem.data, l);
    },
    [load, problem.data],
  );

  /** Put code into the editor for a language (from a reference solution or past submission). */
  const loadCode = useCallback((l: Lang, value: string) => {
    loadSeq.current++; // discard any draft load still in flight
    void saver.current!.flush();
    setLangState(l);
    setCodeState(value);
    saver.current!.schedule(l, value);
    void saver.current!.flush();
  }, []);

  const resetToStarter = useCallback(() => {
    if (problem.data) setCode(problem.data.starters[lang] ?? "");
  }, [lang, problem.data, setCode]);

  const run = useMutation({
    mutationFn: () => {
      void saver.current!.flush();
      return api.run(slug, lang, code, custom);
    },
    onMutate: () => setTab("result"),
    onSuccess: (r) => setRunResult(r),
  });

  const submit = useMutation({
    mutationFn: () => {
      void saver.current!.flush();
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
