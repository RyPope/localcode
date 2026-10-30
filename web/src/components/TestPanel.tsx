import { useState } from "react";
import { Link } from "react-router-dom";
import { fmtValue, formatArgs, type Param, type RunCase, type RunResult, type SubmitResult } from "../api";
import { ICONS } from "../lib/icons";
import styles from "./TestPanel.module.css";
import { Icon } from "./ui";

export type PanelTab = "cases" | "result" | "submission";

function Field({ label, value, tone }: { label: string; value: string; tone?: "good" | "bad" }) {
  return (
    <div className="field">
      <span className={styles.fieldLabel}>{label}</span>
      <pre className={`fv ${tone ?? ""}`}>{value}</pre>
    </div>
  );
}

function ErrorBox({ title, text }: { title: string; text: string }) {
  return (
    <div className="field">
      <span className={styles.errorTitle}>{title}</span>
      <pre className="fv bad">{text}</pre>
    </div>
  );
}

function Verdict({ verdict, children }: { verdict: string; children?: React.ReactNode }) {
  return (
    <div className={styles.verdictRow}>
      <span className={`${styles.verdict} ${verdict === "Accepted" ? styles.accepted : ""}`}>{verdict}</span>
      {children}
    </div>
  );
}

function CasesTab(props: {
  params: Param[];
  examples: unknown[][];
  custom: string[];
  setCustom: (c: string[]) => void;
  total: number;
}) {
  const { params, examples, custom, setCustom } = props;
  const template = examples[0] ? formatArgs(params, examples[0]) : params.map((p) => `${p.name} = `).join(", ");
  return (
    <>
      <span className="note">Run uses these cases · Submit runs all {props.total} hidden tests</span>
      {examples.map((ex, i) => (
        <Field key={`ex${i}`} label={`Case ${i + 1}`} value={formatArgs(params, ex)} />
      ))}
      {custom.map((c, i) => (
        <div key={`c${i}`} className="field">
          <div className="row tight">
            <label className={styles.fieldLabel} htmlFor={`custom${i}`}>
              Case {examples.length + i + 1} · custom
            </label>
            <div className="spacer" />
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
      <div className="row tight">
        <button className="btn" onClick={() => setCustom([...custom, template])}>
          <Icon d={ICONS.plus} /> Add case
        </button>
        {custom.length > 0 && (
          <button className="btn ghost" onClick={() => setCustom([])}>
            Reset to examples
          </button>
        )}
      </div>
      <span className="note">
        Expected output for custom cases comes from the reference solution. Format:{" "}
        <code className="mono">{params.map((p) => `${p.name} = …`).join(", ")}</code>
      </span>
    </>
  );
}

function CaseDetail({ params, c }: { params: Param[]; c: RunCase }) {
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
      {c.ms != null && <span className="muted mono text-xs">{c.ms.toFixed(2)} ms</span>}
    </>
  );
}

function ResultTab({ params, run, customFrom }: { params: Param[]; run: RunResult; customFrom: number }) {
  const [selected, setSelected] = useState(0);
  const index = Math.min(selected, Math.max(0, run.cases.length - 1));
  return (
    <>
      <Verdict verdict={run.verdict}>
        {run.cases.length > 0 && (
          <span className="muted">
            {run.cases.filter((c) => c.ok).length} / {run.cases.length} testcases passed
          </span>
        )}
      </Verdict>
      {run.compile_error && <ErrorBox title="Compile error" text={run.compile_error} />}
      {run.cases.length > 0 && (
        <>
          <div className={styles.caseTabs}>
            {run.cases.map((c, i) => (
              <button key={i} className={`case ${i === index ? "on" : ""}`} onClick={() => setSelected(i)}>
                <span className={`dot ${c.ok ? styles.pass : styles.fail}`} />
                Case {i + 1}
                {i >= customFrom ? " · custom" : ""}
              </button>
            ))}
          </div>
          <CaseDetail params={params} c={run.cases[index]} />
        </>
      )}
    </>
  );
}

function SubmissionTab(props: {
  params: Param[];
  submission: SubmitResult;
  nextHref: string | null;
  onCompare: () => void;
}) {
  const { submission: s, params } = props;
  const failing = s.failing;
  return (
    <>
      <Verdict verdict={s.verdict}>
        <span className="muted">
          {s.passed} / {s.total} testcases passed · full suite, sandboxed, no network
        </span>
      </Verdict>
      {s.compile_error && <ErrorBox title="Compile error" text={s.compile_error} />}
      {s.verdict === "Accepted" && (
        <div className={styles.metrics}>
          <div className={`card ${styles.metric}`}>
            <span className="lbl">Runtime (total)</span>
            <span className={styles.metricValue}>{s.runtime_ms?.toFixed(1)} ms</span>
          </div>
          <div className={`card ${styles.metric}`}>
            <span className="lbl">Peak memory</span>
            <span className={styles.metricValue}>{(s.memory_kb / 1024).toFixed(1)} MB</span>
          </div>
        </div>
      )}
      {failing && (
        <>
          <span className="lbl">First failing case</span>
          <Field label="Input" value={formatArgs(params, failing.args)} />
          {failing.error ? (
            <ErrorBox title="Error" text={failing.error} />
          ) : (
            s.verdict !== "Time Limit Exceeded" && (
              <Field label="Your output" value={fmtValue(failing.actual)} tone="bad" />
            )
          )}
          <Field label="Expected" value={fmtValue(failing.expected)} />
          {failing.stdout && <Field label="Stdout" value={failing.stdout} />}
        </>
      )}
      <div className="row tight">
        {s.verdict === "Accepted" && props.nextHref && (
          <Link className="btn primary" to={props.nextHref}>
            Next problem →
          </Link>
        )}
        <button className="btn" onClick={props.onCompare}>
          Compare with reference solution
        </button>
      </div>
      <span className="note">Runtimes are from your machine and aren't ranked.</span>
    </>
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
  const { tab, setTab, params, examples, run, submission } = props;
  const tabButton = (id: PanelTab, label: string) => (
    <button
      role="tab"
      aria-selected={tab === id}
      className={`tab ${tab === id ? "on" : ""}`}
      onClick={() => setTab(id)}
    >
      {label}
    </button>
  );

  return (
    <div className={styles.panel}>
      <div className="tabs" role="tablist">
        {tabButton("cases", "Testcases")}
        {tabButton("result", "Result")}
        {submission && tabButton("submission", "Submission")}
        <div className="spacer" />
        {props.running && <span className={`note ${styles.running}`}>Running…</span>}
      </div>
      <div className={styles.body}>
        {props.error && <ErrorBox title="Request failed" text={props.error} />}
        {tab === "cases" && (
          <CasesTab
            params={params}
            examples={examples}
            custom={props.custom}
            setCustom={props.setCustom}
            total={props.total}
          />
        )}
        {tab === "result" &&
          (run ? (
            <ResultTab params={params} run={run} customFrom={examples.length} />
          ) : (
            <span className="muted">
              Run your code to see results here. ({examples.length + props.custom.length} cases)
            </span>
          ))}
        {tab === "submission" && submission && (
          <SubmissionTab
            params={params}
            submission={submission}
            nextHref={props.nextHref}
            onCompare={props.onCompare}
          />
        )}
      </div>
    </div>
  );
}
