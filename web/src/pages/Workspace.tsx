import { useQuery } from "@tanstack/react-query";
import { pct } from "../lib/format";
import { ICONS } from "../lib/icons";
import { useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { api, LANG_LABEL, type Lang } from "../api";
import CodeEditor from "../components/CodeEditor";
import SolutionsTab from "../components/SolutionsTab";
import SubmissionsTab from "../components/SubmissionsTab";
import TestPanel from "../components/TestPanel";
import { CompanyBadge, Html, Icon } from "../components/ui";
import { useSplit } from "../hooks/useSplit";
import { useWorkspace, type SaveState } from "../hooks/useWorkspace";
import { oneOf, WINDOWS } from "../lib/filters";
import { pref, setPref } from "../theme";

type LeftTab = "description" | "solutions" | "submissions";

const SAVE_LABEL: Record<SaveState, string> = {
  saved: "Saved locally",
  saving: "Saving…",
  dirty: "Unsaved",
  error: "Couldn't save — retrying",
};

export default function Workspace() {
  const { slug = "" } = useParams();
  const [sp] = useSearchParams();
  const company = sp.get("company");
  const window_ = oneOf(sp.get("window"), WINDOWS, "6m");
  const ws = useWorkspace(slug);
  const [left, setLeft] = useState<LeftTab>("description");
  const [fontSize, setFontSize] = useState<number>(() => pref("fontSize", 14));
  const cols = useSplit("split.cols", 0.42, "x", 0.25, 0.7);
  const rows = useSplit("split.rows", 0.6, "y", 0.2, 0.85);
  const status = useQuery({ queryKey: ["status"], queryFn: api.status });
  const companyCtx = useQuery({
    queryKey: ["company", company, window_],
    queryFn: () => api.company(company!, window_),
    enabled: !!company,
  });
  const p = ws.problem.data;

  if (ws.problem.isError)
    return (
      <main style={{ padding: 24 }}>
        Problem not found. <Link to="/">Back to problems</Link>
      </main>
    );
  if (!p) return null;

  const suffix = company ? `?company=${company}&window=${window_}` : "";
  const nextInList = companyCtx.data?.next_unsolved.find((x) => x.slug !== slug);
  const nextHref = nextInList ? `/problems/${nextInList.slug}${suffix}` : p.next ? `/problems/${p.next}` : null;
  const runnable = p.has_tests && p.langs.includes(ws.lang);
  const langs = p.langs.length ? p.langs : (Object.keys(p.starters) as Lang[]);
  const changeFont = (d: number) => {
    const f = Math.min(22, Math.max(11, fontSize + d));
    setFontSize(f);
    setPref("fontSize", f);
  };

  return (
    <div ref={cols.container} style={{ flex: 1, minHeight: 0, display: "flex", height: "calc(100vh - 49px)" }}>
      {/* left: statement / solutions / submissions */}
      <section
        style={{
          width: `${cols.size * 100}%`,
          minWidth: 0,
          display: "flex",
          flexDirection: "column",
          background: "var(--panel)",
        }}
      >
        <div className="tabs" role="tablist">
          {(["description", "solutions", "submissions"] as LeftTab[]).map((t) => (
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
          <div style={{ flex: 1 }} />
          {p.prev && (
            <Link
              className="btn ghost ibtn"
              style={{ alignSelf: "center" }}
              aria-label="Previous problem"
              to={`/problems/${p.prev}`}
            >
              <Icon d={ICONS.left} />
            </Link>
          )}
          {p.next && (
            <Link
              className="btn ghost ibtn"
              style={{ alignSelf: "center" }}
              aria-label="Next problem"
              to={`/problems/${p.next}`}
            >
              <Icon d={ICONS.right} />
            </Link>
          )}
        </div>
        <div style={{ flex: 1, overflow: "auto" }}>
          {left === "description" && (
            <article style={{ padding: "18px 22px 32px", display: "flex", flexDirection: "column", gap: 14 }}>
              <h1 style={{ margin: 0, fontSize: 20, fontWeight: 600 }}>
                {p.id}. {p.title}
              </h1>
              <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
                <span className={`dpill ${p.difficulty}`}>{p.difficulty}</span>
                {p.status === "solved" && (
                  <span className="tag" style={{ color: "var(--easy)" }}>
                    Solved
                  </span>
                )}
                {p.status === "attempted" && (
                  <span className="tag" style={{ color: "var(--med)" }}>
                    Attempted
                  </span>
                )}
                <span className="muted" style={{ fontSize: 12 }}>
                  Acceptance {pct(p.acceptance)}
                </span>
              </div>
              <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                {p.tags.map((t) => (
                  <Link key={t} className="tag" to={`/?tags=${encodeURIComponent(t)}`}>
                    {t}
                  </Link>
                ))}
              </div>
              {p.companies.length > 0 && (
                <div style={{ display: "flex", gap: 6, flexWrap: "wrap", alignItems: "center" }}>
                  <span className="lbl" style={{ marginRight: 4 }}>
                    Asked by
                  </span>
                  {p.companies.slice(0, 8).map((c) => (
                    <Link key={c.slug} className="tag" to={`/companies/${c.slug}`} style={{ gap: 6 }}>
                      <CompanyBadge name={c.name} size={14} />
                      {c.name}
                    </Link>
                  ))}
                  {p.companies.length > 8 && (
                    <span className="muted" style={{ fontSize: 12 }}>
                      +{p.companies.length - 8} more
                    </span>
                  )}
                </div>
              )}
              <Html html={p.description_html} />
              <footer className="muted" style={{ fontSize: 11.5, borderTop: "1px solid var(--line)", paddingTop: 10 }}>
                Statement via doocs/leetcode (CC BY-SA 4.0) · tests via LeetCodeDataset (Apache-2.0)
              </footer>
            </article>
          )}
          {left === "solutions" && (
            <SolutionsTab
              slug={slug}
              lang={ws.lang}
              onOpen={(l, c) => {
                ws.loadCode(l, c);
              }}
            />
          )}
          {left === "submissions" && <SubmissionsTab slug={slug} onLoad={(l, c) => ws.loadCode(l, c)} />}
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

      {/* right: editor over test panel */}
      <section ref={rows.container} style={{ flex: 1, minWidth: 0, display: "flex", flexDirection: "column" }}>
        <div
          style={{
            height: `${rows.size * 100}%`,
            display: "flex",
            flexDirection: "column",
            minHeight: 0,
            background: "var(--code)",
          }}
        >
          <div className="tabs" style={{ alignItems: "center", gap: 8 }}>
            <label className="sr" htmlFor="lang">
              Language
            </label>
            <select id="lang" className="btn" value={ws.lang} onChange={(e) => ws.setLang(e.target.value as Lang)}>
              {langs.map((l) => (
                <option key={l} value={l}>
                  {LANG_LABEL[l]}
                </option>
              ))}
            </select>
            <button className="btn ghost" onClick={ws.resetToStarter} title="Reset to starter code">
              <Icon d={ICONS.reset} /> Reset
            </button>
            <button className="btn ghost ibtn" aria-label="Smaller font" onClick={() => changeFont(-1)}>
              A−
            </button>
            <span className="mono muted" style={{ fontSize: 11.5 }}>
              {fontSize}px
            </span>
            <button className="btn ghost ibtn" aria-label="Larger font" onClick={() => changeFont(1)}>
              A+
            </button>
            <span className="muted" style={{ fontSize: 12 }}>
              {SAVE_LABEL[ws.save]}
            </span>
            <div style={{ flex: 1 }} />
            <button className="btn" disabled={!runnable || ws.busy} onClick={ws.run} title="Run (⌘↵)">
              <Icon d={ICONS.play} /> Run <span className="kbd">⌘↵</span>
            </button>
            <button className="btn primary" disabled={!runnable || ws.busy} onClick={ws.submit} title="Submit (⌘⇧↵)">
              <Icon d={ICONS.upload} /> Submit
            </button>
          </div>
          <div style={{ flex: 1, minHeight: 0 }}>
            <CodeEditor
              lang={ws.lang}
              value={ws.code}
              onChange={ws.setCode}
              fontSize={fontSize}
              onRun={() => runnable && ws.run()}
              onSubmit={() => runnable && ws.submit()}
            />
          </div>
          <div
            className="mono muted"
            style={{
              display: "flex",
              gap: 14,
              padding: "4px 12px",
              fontSize: 11,
              borderTop: "1px solid var(--line)",
              background: "var(--panel)",
            }}
          >
            <span>{status.data?.toolchains?.[ws.lang] ?? LANG_LABEL[ws.lang]}</span>
            <span>sandboxed · no network</span>
            {!p.has_tests && <span style={{ color: "var(--med)" }}>No tests available — read-only problem</span>}
            {p.has_tests && !p.langs.includes(ws.lang) && (
              <span style={{ color: "var(--med)" }}>{LANG_LABEL[ws.lang]} can't be judged for this problem</span>
            )}
          </div>
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
        <div style={{ flex: 1, minHeight: 0 }}>
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
