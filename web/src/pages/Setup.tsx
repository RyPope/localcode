import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../api";
import { Icon, ICONS } from "../components/ui";

const STEPS = [
  { key: "download", title: "Download sources", detail: "Problem dataset, statements and solutions, company lists" },
  { key: "problems", title: "Problems & test cases", detail: "Hidden suites used by Submit, starter code for 4 languages" },
  { key: "solutions", title: "Statements & reference solutions", detail: "Python, Java, C++, Kotlin, with explanations" },
  { key: "tests", title: "Build the local database", detail: "Merge everything by problem" },
  { key: "companies", title: "Company lists", detail: "Frequency by window: 30 days, 3 months, 6 months, all time" },
];

export const SOURCES = [
  { name: "Test cases & starter code", repo: "newfacade/LeetCodeDataset", url: "https://huggingface.co/datasets/newfacade/LeetCodeDataset", license: "Apache-2.0" },
  { name: "Statements & reference solutions", repo: "doocs/leetcode", url: "https://github.com/doocs/leetcode", license: "CC BY-SA 4.0" },
  { name: "Company frequency lists", repo: "liquidslr/leetcode-company-wise-problems", url: "https://github.com/liquidslr/leetcode-company-wise-problems", license: "No license stated" },
];

export default function Setup() {
  const qc = useQueryClient();
  const status = useQuery({ queryKey: ["status"], queryFn: api.status, refetchInterval: 1500 });
  const retry = useMutation({ mutationFn: api.startImport, onSuccess: () => qc.invalidateQueries({ queryKey: ["status"] }) });
  const imp = status.data?.import;
  const current = STEPS.findIndex((s) => s.key === imp?.step);
  const doneAll = imp?.step === "done" || (!!status.data?.imported && !imp?.running);

  return (
    <div style={{ minHeight: "100%", display: "flex", justifyContent: "center", padding: "56px 24px" }}>
      <div style={{ width: "100%", maxWidth: 1080, display: "flex", flexDirection: "column", gap: 28 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span className="logo-mark" style={{ width: 36, height: 36, borderRadius: 9 }}><Icon d={ICONS.logo} size={20} stroke={2.6} /></span>
          <div>
            <h1 style={{ margin: 0, fontSize: 22, fontWeight: 600 }}>Setting up localcode</h1>
            <p className="muted" style={{ margin: 0 }}>One-time import from open-source datasets into a local database. No account needed.</p>
          </div>
        </div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 20, alignItems: "flex-start" }}>
          <section className="card" style={{ flex: "999 1 560px", padding: 0, gap: 0, overflow: "hidden" }} aria-label="Import progress">
            <div style={{ padding: "18px 20px" }}>
              <h2 style={{ margin: 0, fontSize: 15, fontWeight: 600 }}>{doneAll ? "Ready" : imp?.error ? "Import failed" : "Importing"}</h2>
              {imp?.error && <p className="bad" style={{ margin: "6px 0 0" }}>{imp.error}</p>}
            </div>
            <ol style={{ listStyle: "none", margin: 0, padding: 0 }}>
              {STEPS.map((s, i) => {
                const state = doneAll || i < current ? "done" : i === current ? "run" : "wait";
                return (
                  <li key={s.key} style={{ display: "grid", gridTemplateColumns: "28px minmax(0,1fr) auto", gap: 12, padding: "14px 20px",
                    borderTop: "1px solid var(--line)", background: state === "run" ? "var(--acc-bg)" : undefined }}>
                    <span style={{ width: 22, height: 22, borderRadius: 11, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 11, fontWeight: 600,
                      background: state === "done" ? "var(--easy-bg)" : undefined, color: state === "done" ? "var(--easy)" : state === "run" ? "var(--acc)" : "var(--fg3)",
                      border: state === "run" ? "2px solid var(--acc)" : state === "wait" ? "1px solid var(--line2)" : undefined }}>
                      {state === "done" ? <Icon d={ICONS.check} size={12} stroke={3} /> : i + 1}
                    </span>
                    <div>
                      <div style={{ fontWeight: 500, color: state === "wait" ? "var(--fg2)" : undefined }}>{s.title}</div>
                      <div className="muted" style={{ fontSize: 12 }}>{s.detail}</div>
                      {state === "run" && imp && imp.total > 0 && (
                        <div className="bar" style={{ marginTop: 8 }}><span style={{ width: `${(imp.done / imp.total) * 100}%` }} /></div>
                      )}
                    </div>
                    <span className="mono muted" style={{ fontSize: 12 }}>{state === "run" && imp?.total ? `${imp.done.toLocaleString()} / ${imp.total.toLocaleString()}` : ""}</span>
                  </li>
                );
              })}
            </ol>
            <pre className="mono" aria-label="Import log" style={{ margin: "0 20px", padding: "10px 12px", borderRadius: 8, background: "var(--bg)",
              border: "1px solid var(--line)", fontSize: 11.5, lineHeight: 1.7, color: "var(--fg3)", whiteSpace: "pre-wrap", maxHeight: 160, overflow: "auto" }}>
              {(imp?.log ?? []).slice(-8).join("\n") || "starting…"}
            </pre>
            <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "16px 20px", flexWrap: "wrap" }}>
              <span className="muted" style={{ fontSize: 12 }}>The first import downloads about 200 MB and takes a few minutes.</span>
              <div style={{ flex: 1 }} />
              {imp?.error && <button className="btn" onClick={() => retry.mutate()}>Retry</button>}
              <a className={`btn primary lg`} href="/" aria-disabled={!doneAll} style={{ pointerEvents: doneAll ? undefined : "none", opacity: doneAll ? 1 : 0.5 }}>
                Start practising
              </a>
            </div>
          </section>
          <aside className="card" style={{ flex: "1 1 320px" }}>
            <h2 className="lbl">Sources &amp; licenses</h2>
            <p className="muted" style={{ margin: 0, fontSize: 12.5 }}>
              Content is downloaded from these public repositories at setup time; localcode itself ships no problem content.
            </p>
            {SOURCES.map((s) => (
              <div key={s.repo} style={{ borderTop: "1px solid var(--line)", paddingTop: 10, fontSize: 12.5 }}>
                <div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}>
                  <span style={{ fontWeight: 500 }}>{s.name}</span>
                  <span className="mono muted" style={{ fontSize: 11.5 }}>{s.license}</span>
                </div>
                <a href={s.url} target="_blank" rel="noreferrer">{s.repo}</a>
              </div>
            ))}
          </aside>
        </div>
      </div>
    </div>
  );
}
