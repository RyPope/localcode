import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "../api";
import { CompanyBadge, Icon, ICONS } from "../components/ui";

const DIFFS = [["easy", "Easy", "var(--easy)"], ["medium", "Medium", "var(--med)"], ["hard", "Hard", "var(--hard)"]] as const;

export default function Progress() {
  const stats = useQuery({ queryKey: ["stats"], queryFn: api.stats });
  const status = useQuery({ queryKey: ["status"], queryFn: api.status, refetchInterval: (q) => (q.state.data?.import.running ? 1500 : false) });
  const qc = useQueryClient();
  const update = useMutation({ mutationFn: api.startImport, onSuccess: () => qc.invalidateQueries({ queryKey: ["status"] }) });
  const s = stats.data;
  if (!s) return null;
  const solved = s.totals.easy[0] + s.totals.medium[0] + s.totals.hard[0];
  const total = s.totals.easy[1] + s.totals.medium[1] + s.totals.hard[1];
  const weekMax = Math.max(5, ...s.solved_by_week.map((w) => w.easy + w.medium + w.hard));
  const yMax = Math.ceil(weekMax / 5) * 5;
  const imp = status.data?.import;

  return (
    <main style={{ width: "100%", maxWidth: 1280, margin: "0 auto", padding: "24px 24px 40px", display: "flex", flexDirection: "column", gap: 16 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
        <h1 style={{ margin: 0, fontSize: 22, fontWeight: 600 }}>Progress</h1>
        <span className="muted" style={{ fontSize: 12.5 }}>
          {s.since ? `Since ${new Date(s.since).toLocaleDateString()} · ` : ""}all data stays on this machine
        </span>
        <div style={{ flex: 1 }} />
        <a className="btn" href="/api/export" download="localcode-progress.json"><Icon d={ICONS.download} /> Export progress</a>
      </div>

      <section style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(min(220px, 100%), 1fr))", gap: 12 }}>
        <div className="card" style={{ gap: 6 }}>
          <h2 className="lbl">Solved</h2>
          <div style={{ fontSize: 28, fontWeight: 600 }}>{solved} <span className="muted" style={{ fontSize: 14, fontWeight: 400 }}>/ {total.toLocaleString()}</span></div>
          <div className="bar"><span style={{ width: `${total ? (solved / total) * 100 : 0}%` }} /></div>
        </div>
        {DIFFS.map(([k, label, color]) => (
          <div className="card" style={{ gap: 6 }} key={k}>
            <h2 className="lbl">{label}</h2>
            <div style={{ fontSize: 28, fontWeight: 600 }}>{s.totals[k][0]} <span className="muted" style={{ fontSize: 14, fontWeight: 400 }}>/ {s.totals[k][1].toLocaleString()}</span></div>
            <div className="bar"><span style={{ width: `${s.totals[k][1] ? (s.totals[k][0] / s.totals[k][1]) * 100 : 0}%`, background: color }} /></div>
          </div>
        ))}
      </section>

      <section className="card">
        <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
          <h2 style={{ margin: 0, fontSize: 14, fontWeight: 600 }}>Solved over time</h2>
          <span className="muted" style={{ fontSize: 12 }}>Problems first accepted per week · last 26 weeks</span>
          <div style={{ flex: 1 }} />
          {DIFFS.map(([k, label, color]) => (
            <span key={k} style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, color: "var(--fg2)" }}>
              <span style={{ width: 10, height: 10, borderRadius: 2, background: color }} />{label}
            </span>
          ))}
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "28px minmax(0, 1fr)", gap: 8 }}>
          <div className="mono muted" style={{ display: "flex", flexDirection: "column", justifyContent: "space-between", height: 180, fontSize: 11, textAlign: "right" }}>
            <span>{yMax}</span><span>{yMax / 2}</span><span>0</span>
          </div>
          <div role="img" aria-label={`${solved} problems solved, by week and difficulty`}
            style={{ height: 180, display: "flex", alignItems: "flex-end", gap: 4, borderBottom: "1px solid var(--line2)" }}>
            {s.solved_by_week.map((w) => (
              <div key={w.week} title={`Week of ${w.week}: ${w.easy} easy, ${w.medium} medium, ${w.hard} hard`}
                style={{ flex: 1, height: "100%", display: "flex", flexDirection: "column-reverse", gap: 1 }}>
                {DIFFS.map(([k, , color]) => <span key={k} style={{ height: `${(w[k] / yMax) * 100}%`, background: color, borderRadius: 2 }} />)}
              </div>
            ))}
          </div>
        </div>
      </section>

      <section style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(min(460px, 100%), 1fr))", gap: 12 }}>
        <div className="card">
          <div style={{ display: "flex", justifyContent: "space-between" }}><h2 style={{ margin: 0, fontSize: 14, fontWeight: 600 }}>By topic</h2><span className="muted" style={{ fontSize: 12 }}>solved / total</span></div>
          {s.by_topic.map((t) => (
            <div key={t.name} style={{ display: "grid", gridTemplateColumns: "150px minmax(0,1fr) 84px", gap: 12, alignItems: "center", fontSize: 12.5 }}>
              <Link to={`/?tags=${encodeURIComponent(t.name)}`} style={{ color: "var(--fg)" }}>{t.name}</Link>
              <div className="bar"><span style={{ width: `${(t.solved / t.total) * 100}%` }} /></div>
              <span className="mono" style={{ fontSize: 11.5, color: "var(--fg2)", textAlign: "right" }}>{t.solved} / {t.total.toLocaleString()}</span>
            </div>
          ))}
        </div>
        <div className="card">
          <div style={{ display: "flex", justifyContent: "space-between" }}><h2 style={{ margin: 0, fontSize: 14, fontWeight: 600 }}>By company</h2><span className="muted" style={{ fontSize: 12 }}>Problems asked in the last 6 months</span></div>
          {s.by_company.length === 0 && <span className="muted">Solve a problem to see company coverage.</span>}
          {s.by_company.map((c) => (
            <div key={c.slug} style={{ display: "grid", gridTemplateColumns: "24px minmax(0,1fr) 80px 140px", gap: 12, alignItems: "center", fontSize: 12.5 }}>
              <CompanyBadge name={c.name} size={22} />
              <Link to={`/companies/${c.slug}`} style={{ color: "var(--fg)", fontWeight: 500 }}>{c.name}</Link>
              <span className="mono" style={{ textAlign: "right", color: "var(--fg2)" }}><b style={{ color: "var(--fg)", fontWeight: 500 }}>{c.solved}</b> / {c.total}</span>
              <div className="bar"><span style={{ width: `${(c.solved / c.total) * 100}%` }} /></div>
            </div>
          ))}
          <Link to="/companies" style={{ fontSize: 12.5 }}>See all companies →</Link>
        </div>
      </section>

      <section className="card" style={{ flexDirection: "row", alignItems: "center", flexWrap: "wrap", gap: 12 }}>
        <div style={{ flex: 1, minWidth: 240 }}>
          <div style={{ fontWeight: 600 }}>Problem data</div>
          <div className="muted" style={{ fontSize: 12 }}>
            {status.data?.meta.stats ? `${status.data.meta.stats.problems.toLocaleString()} problems · ${status.data.meta.stats.companies} companies · ` : ""}
            imported {status.data?.meta.imported_at ? new Date(status.data.meta.imported_at).toLocaleString() : "—"}.
            Updating never touches your submissions or drafts.
          </div>
          {imp?.running && <div style={{ fontSize: 12, marginTop: 4 }}>Updating: {imp.step} {imp.total ? `${imp.done}/${imp.total}` : ""}</div>}
          {imp?.error && <div className="bad" style={{ fontSize: 12, marginTop: 4 }}>Last update failed: {imp.error}</div>}
        </div>
        <button className="btn" disabled={imp?.running || update.isPending} onClick={() => update.mutate()}>
          <Icon d={ICONS.refresh} /> {imp?.running ? "Updating…" : "Check for updates"}
        </button>
      </section>
    </main>
  );
}
