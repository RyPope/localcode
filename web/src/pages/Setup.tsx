import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../api";
import { Meter } from "../components/layout";
import { Icon } from "../components/ui";
import { ICONS } from "../lib/icons";
import { SOURCES } from "../lib/sources";
import styles from "./Setup.module.css";

const STEPS = [
  { key: "download", title: "Download sources", detail: "Problem dataset, statements and solutions, company lists" },
  {
    key: "problems",
    title: "Problems & test cases",
    detail: "Hidden suites used by Submit, starter code for 4 languages",
  },
  {
    key: "solutions",
    title: "Statements & reference solutions",
    detail: "Python, Java, C++, Kotlin, with explanations",
  },
  { key: "tests", title: "Build the local database", detail: "Merge everything by problem" },
  { key: "companies", title: "Company lists", detail: "Frequency by window: 30 days, 3 months, 6 months, all time" },
];
const LOG_LINES = 8;

type StepState = "done" | "run" | "wait";

export default function Setup() {
  const qc = useQueryClient();
  const status = useQuery({ queryKey: ["status"], queryFn: api.status, refetchInterval: 1500 });
  const retry = useMutation({
    mutationFn: api.startImport,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["status"] }),
  });
  const imp = status.data?.import;
  const current = STEPS.findIndex((s) => s.key === imp?.step);
  const finished = imp?.step === "done" || (!!status.data?.imported && !imp?.running);
  const stateOf = (i: number): StepState => (finished || i < current ? "done" : i === current ? "run" : "wait");

  return (
    <div className={styles.screen}>
      <div className={styles.content}>
        <div className="row">
          <span className={`logo-mark ${styles.brand}`}>
            <Icon d={ICONS.logo} size={20} stroke={2.6} />
          </span>
          <div>
            <h1 className="title-1">Setting up localcode</h1>
            <p className={styles.lede}>
              One-time import from open-source datasets into a local database. No account needed.
            </p>
          </div>
        </div>
        <div className={styles.columns}>
          <section className={`card ${styles.progress}`} aria-label="Import progress">
            <div className={styles.progressHead}>
              <h2 className="title-2">{finished ? "Ready" : imp?.error ? "Import failed" : "Importing"}</h2>
              {imp?.error && <p className={`bad ${styles.error}`}>{imp.error}</p>}
            </div>
            <ol className={styles.steps}>
              {STEPS.map((s, i) => {
                const state = stateOf(i);
                return (
                  <li key={s.key} className={`${styles.step} ${styles[state]}`}>
                    <span className={styles.marker}>
                      {state === "done" ? <Icon d={ICONS.check} size={12} stroke={3} /> : i + 1}
                    </span>
                    <div>
                      <div className={styles.stepTitle}>{s.title}</div>
                      <div className="note">{s.detail}</div>
                      {state === "run" && imp && imp.total > 0 && (
                        <div className={styles.stepBar}>
                          <Meter ratio={imp.done / imp.total} />
                        </div>
                      )}
                    </div>
                    <span className="mono note">
                      {state === "run" && imp?.total
                        ? `${imp.done.toLocaleString()} / ${imp.total.toLocaleString()}`
                        : ""}
                    </span>
                  </li>
                );
              })}
            </ol>
            <pre className={`mono ${styles.log}`} aria-label="Import log">
              {(imp?.log ?? []).slice(-LOG_LINES).join("\n") || "starting…"}
            </pre>
            <div className={`row tight ${styles.footer}`}>
              <span className="note">The first import downloads about 200 MB and takes a few minutes.</span>
              <div className="spacer" />
              {imp?.error && (
                <button className="btn" onClick={() => retry.mutate()}>
                  Retry
                </button>
              )}
              <a className={`btn primary lg ${finished ? "" : styles.disabled}`} href="/" aria-disabled={!finished}>
                Start practising
              </a>
            </div>
          </section>
          <aside className={`card ${styles.sources}`}>
            <h2 className="lbl">Sources &amp; licenses</h2>
            <p className="note text-sm">
              Content is downloaded from these public repositories at setup time; localcode itself ships no problem
              content.
            </p>
            {SOURCES.map((s) => (
              <div key={s.repo} className={styles.source}>
                <div className="row spread">
                  <span className="strong">{s.name}</span>
                  <span className="mono muted text-xs">{s.license}</span>
                </div>
                <a href={s.url} target="_blank" rel="noreferrer">
                  {s.repo}
                </a>
              </div>
            ))}
          </aside>
        </div>
      </div>
    </div>
  );
}
