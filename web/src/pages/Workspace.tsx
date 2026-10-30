import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { api, LANG_LABEL, type Lang, type ProblemDetail } from "../api";
import CodeEditor from "../components/CodeEditor";
import { EditorStatusBar, EditorToolbar } from "../components/EditorToolbar";
import ProblemDescription from "../components/ProblemDescription";
import SolutionsTab from "../components/SolutionsTab";
import SubmissionsTab from "../components/SubmissionsTab";
import TestPanel from "../components/TestPanel";
import { Icon } from "../components/ui";
import { useSplit } from "../hooks/useSplit";
import { useWorkspace } from "../hooks/useWorkspace";
import { oneOf, WINDOWS } from "../lib/filters";
import { ICONS } from "../lib/icons";
import { pref, setPref } from "../theme";
import styles from "./Workspace.module.css";

type LeftTab = "description" | "solutions" | "submissions";
const LEFT_TABS: LeftTab[] = ["description", "solutions", "submissions"];
const FONT_RANGE = { min: 11, max: 22 };

function judgeWarning(p: ProblemDetail, lang: Lang): string | null {
  if (!p.has_tests) return "No tests available — read-only problem";
  if (!p.langs.includes(lang)) return `${LANG_LABEL[lang]} can't be judged for this problem`;
  return null;
}

export default function Workspace() {
  const { slug = "" } = useParams();
  const [sp] = useSearchParams();
  const company = sp.get("company");
  const window = oneOf(sp.get("window"), WINDOWS, "6m");
  const ws = useWorkspace(slug);
  const [left, setLeft] = useState<LeftTab>("description");
  const [fontSize, setFontSize] = useState<number>(() => pref("fontSize", 14));
  const cols = useSplit("split.cols", 0.42, "x", 0.25, 0.7);
  const rows = useSplit("split.rows", 0.6, "y", 0.2, 0.85);
  const status = useQuery({ queryKey: ["status"], queryFn: api.status });
  const companyCtx = useQuery({
    queryKey: ["company", company, window],
    queryFn: () => api.company(company!, window),
    enabled: !!company,
  });
  const p = ws.problem.data;

  if (ws.problem.isError)
    return (
      <main className="page">
        Problem not found. <Link to="/">Back to problems</Link>
      </main>
    );
  if (!p) return null;

  const suffix = company ? `?company=${company}&window=${window}` : "";
  const nextInList = companyCtx.data?.next_unsolved.find((x) => x.slug !== slug);
  const nextHref = nextInList ? `/problems/${nextInList.slug}${suffix}` : p.next ? `/problems/${p.next}` : null;
  const canRun = p.has_tests && p.langs.includes(ws.lang) && !ws.busy;
  const langs = p.langs.length ? p.langs : (Object.keys(p.starters) as Lang[]);
  const changeFont = (delta: number) => {
    const size = Math.min(FONT_RANGE.max, Math.max(FONT_RANGE.min, fontSize + delta));
    setFontSize(size);
    setPref("fontSize", size);
  };

  return (
    <div ref={cols.container} className={styles.workspace}>
      <section className={styles.left} style={{ width: `${cols.size * 100}%` }}>
        <div className="tabs" role="tablist">
          {LEFT_TABS.map((t) => (
            <button
              key={t}
              role="tab"
              aria-selected={left === t}
              className={`tab ${left === t ? "on" : ""}`}
              onClick={() => setLeft(t)}
            >
              {t[0].toUpperCase() + t.slice(1)}
            </button>
          ))}
          <div className="spacer" />
          {p.prev && (
            <Link
              className={`btn ghost ibtn ${styles.navButton}`}
              aria-label="Previous problem"
              to={`/problems/${p.prev}`}
            >
              <Icon d={ICONS.left} />
            </Link>
          )}
          {p.next && (
            <Link className={`btn ghost ibtn ${styles.navButton}`} aria-label="Next problem" to={`/problems/${p.next}`}>
              <Icon d={ICONS.right} />
            </Link>
          )}
        </div>
        <div className={styles.scroll}>
          {left === "description" && <ProblemDescription problem={p} />}
          {left === "solutions" && <SolutionsTab slug={slug} lang={ws.lang} onOpen={ws.loadCode} />}
          {left === "submissions" && <SubmissionsTab slug={slug} onLoad={ws.loadCode} />}
        </div>
      </section>

      <div
        className="splitv"
        role="separator"
        aria-orientation="vertical"
        aria-label="Resize panels"
        onPointerDown={cols.onPointerDown}
      >
        <span />
      </div>

      <section ref={rows.container} className={styles.right}>
        <div className={styles.editorPane} style={{ height: `${rows.size * 100}%` }}>
          <EditorToolbar
            langs={langs}
            lang={ws.lang}
            onLang={ws.setLang}
            onReset={ws.resetToStarter}
            fontSize={fontSize}
            onFontSize={changeFont}
            save={ws.save}
            canRun={canRun}
            onRun={ws.run}
            onSubmit={ws.submit}
          />
          <div className={styles.fill}>
            <CodeEditor
              lang={ws.lang}
              value={ws.code}
              onChange={ws.setCode}
              fontSize={fontSize}
              onRun={() => canRun && ws.run()}
              onSubmit={() => canRun && ws.submit()}
            />
          </div>
          <EditorStatusBar
            toolchain={status.data?.toolchains?.[ws.lang] ?? LANG_LABEL[ws.lang]}
            warning={judgeWarning(p, ws.lang)}
          />
        </div>
        <div
          className="splith"
          role="separator"
          aria-orientation="horizontal"
          aria-label="Resize editor"
          onPointerDown={rows.onPointerDown}
        >
          <span />
        </div>
        <div className={styles.fill}>
          <TestPanel
            tab={ws.tab}
            setTab={ws.setTab}
            params={p.params}
            examples={p.examples}
            custom={ws.custom}
            setCustom={ws.setCustom}
            run={ws.runResult}
            submission={ws.submission}
            running={ws.busy}
            total={p.test_count}
            nextHref={nextHref}
            onCompare={() => setLeft("solutions")}
            error={ws.error}
          />
        </div>
      </section>
    </div>
  );
}
