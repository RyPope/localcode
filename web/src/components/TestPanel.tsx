import { useState } from "react";
import { ICONS } from "../lib/icons";
import { Link } from "react-router-dom";
import { fmtValue, formatArgs, type Param, type RunResult, type SubmitResult } from "../api";
import { Icon } from "./ui";

export type PanelTab = "cases" | "result" | "submission";

const VERDICT_COLOR = (v: string) => (v === "Accepted" ? "var(--easy)" : "var(--hard)");

function Field({ label, value, tone }: { label: string; value: string; tone?: "good" | "bad" }) {
  return (
    <div className="field">
      <span className="lbl" style={{ textTransform: "none", letterSpacing: 0, fontSize: 11.5 }}>
        {label}
      </span>
      <pre className={`fv ${tone ?? ""}`}>{value}</pre>
    </div>
  );
}

function ErrorBox({ title, text }: { title: string; text: string }) {
  return (
    <div className="field">
      <span style={{ color: "var(--hard)", fontWeight: 600 }}>{title}</span>
      <pre className="fv bad">{text}</pre>
    </div>
  );
}

export default function TestPanel(props: {
  tab: PanelTab;
  setTab: (t: PanelTab) => void;
  params: Param[];
  examples: unknown[][];
  custom: string[];
  setCustom: (c: string[]) => void;
  run: RunResult | null;
  submission: SubmitResult | null;
  running: boolean;
  total: number;
  nextHref: string | null;
  onCompare: () => void;
  error: string | null;
}) {
  const { tab, setTab, params, examples, custom, setCustom, run, submission } = props;
  const [sel, setSel] = useState(0);
  const caseCount = examples.length + custom.length;
  const runSel = Math.min(sel, Math.max(0, (run?.cases.length ?? 1) - 1));

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", minHeight: 0, background: "var(--panel)" }}>
      <div className="tabs" role="tablist">
        <button role="tab" className={`tab ${tab === "cases" ? "on" : ""}`} onClick={() => setTab("cases")}>
          Testcases
        </button>
        <button role="tab" className={`tab ${tab === "result" ? "on" : ""}`} onClick={() => setTab("result")}>
          Result
        </button>
        {submission && (
          <button role="tab" className={`tab ${tab === "submission" ? "on" : ""}`} onClick={() => setTab("submission")}>
            Submission
          </button>
        )}
        <div style={{ flex: 1 }} />
        {props.running && (
          <span className="muted" style={{ alignSelf: "center", fontSize: 12 }}>
            Running…
          </span>
        )}
      </div>
      <div
        style={{ flex: 1, overflow: "auto", padding: "12px 16px", display: "flex", flexDirection: "column", gap: 12 }}
      >
        {props.error && <ErrorBox title="Request failed" text={props.error} />}

        {tab === "cases" && (
          <>
            <span className="muted" style={{ fontSize: 12 }}>
              Run uses these cases · Submit runs all {props.total} hidden tests
            </span>
            {examples.map((ex, i) => (
              <Field key={`ex${i}`} label={`Case ${i + 1}`} value={formatArgs(params, ex)} />
            ))}
            {custom.map((c, i) => (
              <div key={`c${i}`} className="field">
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <label
                    className="lbl"
                    htmlFor={`custom${i}`}
                    style={{ textTransform: "none", letterSpacing: 0, fontSize: 11.5 }}
                  >
                    Case {examples.length + i + 1} · custom
                  </label>
                  <div style={{ flex: 1 }} />
                  <button
                    className="btn ghost ibtn"
                    aria-label="Remove case"
                    onClick={() => setCustom(custom.filter((_, j) => j !== i))}
                  >
                    <Icon d={ICONS.x} />
                  </button>
                </div>
                <textarea
                  id={`custom${i}`}
                  className="ta"
                  rows={2}
                  value={c}
                  spellCheck={false}
                  onChange={(e) => setCustom(custom.map((x, j) => (j === i ? e.target.value : x)))}
                />
              </div>
            ))}
            <div style={{ display: "flex", gap: 8 }}>
              <button
                className="btn"
                onClick={() =>
                  setCustom([
                    ...custom,
                    examples[0] ? formatArgs(params, examples[0]) : params.map((p) => `${p.name} = `).join(", "),
                  ])
                }
              >
                <Icon d={ICONS.plus} /> Add case
              </button>
              {custom.length > 0 && (
                <button className="btn ghost" onClick={() => setCustom([])}>
                  Reset to examples
                </button>
              )}
            </div>
            <span className="muted" style={{ fontSize: 12 }}>
              Expected output for custom cases comes from the reference solution. Format:{" "}
              <code className="mono">{params.map((p) => `${p.name} = …`).join(", ")}</code>
            </span>
          </>
        )}

        {tab === "result" && !run && (
          <span className="muted">Run your code to see results here. ({caseCount} cases)</span>
        )}
        {tab === "result" && run && (
          <>
            <div style={{ display: "flex", alignItems: "baseline", gap: 10 }}>
              <span style={{ fontSize: 17, fontWeight: 600, color: VERDICT_COLOR(run.verdict) }}>{run.verdict}</span>
              {run.cases.length > 0 && (
                <span className="muted">
                  {run.cases.filter((c) => c.ok).length} / {run.cases.length} testcases passed
                </span>
              )}
            </div>
            {run.compile_error && <ErrorBox title="Compile error" text={run.compile_error} />}
            {run.cases.length > 0 && (
              <>
                <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
                  {run.cases.map((c, i) => (
                    <button key={i} className={`case ${i === runSel ? "on" : ""}`} onClick={() => setSel(i)}>
                      <span className="dot" style={{ background: c.ok ? "var(--easy)" : "var(--hard)" }} />
                      Case {i + 1}
                      {i >= examples.length ? " · custom" : ""}
                    </button>
                  ))}
                </div>
                {(() => {
                  const c = run.cases[runSel];
                  return (
                    <>
                      <Field label="Input" value={formatArgs(params, c.args)} />
                      {c.error ? (
                        <ErrorBox title="Error" text={c.error} />
                      ) : (
                        <Field label="Your output" value={fmtValue(c.actual)} tone={c.ok ? "good" : "bad"} />
                      )}
                      <Field label="Expected" value={c.expected === null && c.error ? "—" : fmtValue(c.expected)} />
                      {c.stdout && <Field label="Stdout" value={c.stdout} />}
                      {c.ms != null && (
                        <span className="muted mono" style={{ fontSize: 11.5 }}>
                          {c.ms.toFixed(2)} ms
                        </span>
                      )}
                    </>
                  );
                })()}
              </>
            )}
          </>
        )}

        {tab === "submission" && submission && (
          <>
            <div style={{ display: "flex", alignItems: "baseline", gap: 10, flexWrap: "wrap" }}>
              <span style={{ fontSize: 17, fontWeight: 600, color: VERDICT_COLOR(submission.verdict) }}>
                {submission.verdict}
              </span>
              <span className="muted">
                {submission.passed} / {submission.total} testcases passed · full suite, sandboxed, no network
              </span>
            </div>
            {submission.compile_error && <ErrorBox title="Compile error" text={submission.compile_error} />}
            {submission.verdict === "Accepted" && (
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: 10 }}>
                <div className="card" style={{ gap: 2, padding: "10px 12px" }}>
                  <span className="lbl">Runtime (total)</span>
                  <span style={{ fontSize: 18, fontWeight: 600 }}>{submission.runtime_ms?.toFixed(1)} ms</span>
                </div>
                <div className="card" style={{ gap: 2, padding: "10px 12px" }}>
                  <span className="lbl">Peak memory</span>
                  <span style={{ fontSize: 18, fontWeight: 600 }}>{(submission.memory_kb / 1024).toFixed(1)} MB</span>
                </div>
              </div>
            )}
            {submission.failing && (
              <>
                <span className="lbl">First failing case</span>
                <Field label="Input" value={formatArgs(params, submission.failing.args)} />
                {submission.failing.error ? (
                  <ErrorBox title="Error" text={submission.failing.error} />
                ) : (
                  submission.verdict !== "Time Limit Exceeded" && (
                    <Field label="Your output" value={fmtValue(submission.failing.actual)} tone="bad" />
                  )
                )}
                <Field label="Expected" value={fmtValue(submission.failing.expected)} />
                {submission.failing.stdout && <Field label="Stdout" value={submission.failing.stdout} />}
              </>
            )}
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              {submission.verdict === "Accepted" && props.nextHref && (
                <Link className="btn primary" to={props.nextHref}>
                  Next problem →
                </Link>
              )}
              <button className="btn" onClick={props.onCompare}>
                Compare with reference solution
              </button>
            </div>
            <span className="muted" style={{ fontSize: 12 }}>
              Runtimes are from your machine and aren't ranked.
            </span>
          </>
        )}
      </div>
    </div>
  );
}
