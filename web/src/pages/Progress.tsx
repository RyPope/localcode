import { refreshSummary } from "../lib/labels";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api, type Stats } from "../api";
import { CardHeader, Meter, PageHeader, Stat } from "../components/layout";
import QueryState from "../components/QueryState";
import { useAppStatus } from "../hooks/useAppStatus";
import { CompanyBadge, Icon } from "../components/ui";
import { ICONS } from "../lib/icons";
import styles from "./Progress.module.css";

const DIFFS = [
  ["easy", "Easy", "var(--easy)"],
  ["medium", "Medium", "var(--med)"],
  ["hard", "Hard", "var(--hard)"],
] as const;

export default function Progress() {
  const stats = useQuery({ queryKey: ["stats"], queryFn: api.stats });
  return <QueryState query={stats}>{(s) => <ProgressView stats={s} />}</QueryState>;
}

function ProgressView({ stats: s }: { stats: Stats }) {
  const status = useAppStatus();
  const qc = useQueryClient();
  const update = useMutation({
    mutationFn: api.startImport,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["status"] }),
  });
  const solved = s.totals.easy[0] + s.totals.medium[0] + s.totals.hard[0];
  const total = s.totals.easy[1] + s.totals.medium[1] + s.totals.hard[1];
  const weekMax = Math.max(5, ...s.solved_by_week.map((w) => w.easy + w.medium + w.hard));
  const yMax = Math.ceil(weekMax / 5) * 5;
  const imp = status.data?.import;
  const meta = status.data?.meta;

  return (
    <main className="page">
      <PageHeader
        title="Progress"
        subtitle={`${s.since ? `Since ${new Date(s.since).toLocaleDateString()} · ` : ""}all data stays on this machine`}
      >
        <a className="btn" href="/api/export" download="localcode-progress.json">
          <Icon d={ICONS.download} /> Export progress
        </a>
      </PageHeader>

      <section className="grid">
        <div className="card stack">
          <h2 className="lbl">Solved</h2>
          <Stat value={solved} of={total} />
          <Meter ratio={solved / total} />
        </div>
        {DIFFS.map(([k, label, color]) => (
          <div className="card stack" key={k}>
            <h2 className="lbl">{label}</h2>
            <Stat value={s.totals[k][0]} of={s.totals[k][1]} />
            <Meter ratio={s.totals[k][0] / s.totals[k][1]} color={color} />
          </div>
        ))}
      </section>

      <section className="card">
        <div className="row">
          <h2 className="title-3">Solved over time</h2>
          <span className="note">Problems first accepted per week · last 26 weeks</span>
          <div className="spacer" />
          {DIFFS.map(([k, label, color]) => (
            <span key={k} className={styles.legend}>
              <span className={styles.swatch} style={{ background: color }} />
              {label}
            </span>
          ))}
        </div>
        <div className={styles.chart}>
          <div className={`mono ${styles.axis}`}>
            <span>{yMax}</span>
            <span>{yMax / 2}</span>
            <span>0</span>
          </div>
          <div className={styles.plot} role="img" aria-label={`${solved} problems solved, by week and difficulty`}>
            {s.solved_by_week.map((w) => (
              <div
                key={w.week}
                className={styles.week}
                title={`Week of ${w.week}: ${w.easy} easy, ${w.medium} medium, ${w.hard} hard`}
              >
                {DIFFS.map(([k, , color]) => (
                  <span key={k} style={{ height: `${(w[k] / yMax) * 100}%`, background: color }} />
                ))}
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className={`grid ${styles.wideGrid}`}>
        <div className="card">
          <CardHeader title="By topic" note="solved / total" />
          {s.by_topic.map((t) => (
            <div key={t.name} className={styles.topicRow}>
              <Link className="fg" to={`/?tags=${encodeURIComponent(t.name)}`}>
                {t.name}
              </Link>
              <Meter ratio={t.solved / t.total} />
              <span className={styles.count}>
                {t.solved} / {t.total.toLocaleString()}
              </span>
            </div>
          ))}
        </div>
        <div className="card">
          <CardHeader title="By company" note="Problems asked in the last 6 months" />
          {s.by_company.length === 0 && <span className="note">Solve a problem to see company coverage.</span>}
          {s.by_company.map((c) => (
            <div key={c.slug} className={styles.companyRow}>
              <CompanyBadge name={c.name} size={22} />
              <Link className="fg strong" to={`/companies/${c.slug}`}>
                {c.name}
              </Link>
              <span className={styles.count}>
                <b>{c.solved}</b> / {c.total}
              </span>
              <Meter ratio={c.solved / c.total} />
            </div>
          ))}
          <Link className="text-sm" to="/companies">
            See all companies →
          </Link>
        </div>
      </section>

      <section className={`card ${styles.dataCard}`}>
        <div className={styles.dataText}>
          <div className="strong">Problem data</div>
          <div className="note">
            {meta?.stats ? `${refreshSummary(meta.stats).join(" · ")} · ` : ""}
            imported {meta?.imported_at ? new Date(meta.imported_at).toLocaleString() : "—"}. Refreshing downloads every
            source and re-reads the repo&apos;s content/ folder. It adds and updates problems but never removes any, and
            never touches your submissions or drafts.
          </div>
          {meta?.stats?.skipped && meta.stats.skipped.length > 0 && (
            <div className="note bad">
              Skipped {meta.stats.skipped.length} local file{meta.stats.skipped.length === 1 ? "" : "s"}:
              <ul className={styles.skipped}>
                {meta.stats.skipped.map((s) => (
                  <li key={s.path}>
                    <code>{s.path}</code>: {s.reason}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {imp?.running && (
            <div className="note">
              Refreshing: {imp.step} {imp.total ? `${imp.done}/${imp.total}` : ""}
            </div>
          )}
          {imp?.error && <div className="note bad">Last refresh failed: {imp.error}</div>}
        </div>
        <button className="btn" disabled={imp?.running || update.isPending} onClick={() => update.mutate()}>
          <Icon d={ICONS.refresh} /> {imp?.running ? "Refreshing…" : "Refresh content"}
        </button>
      </section>
    </main>
  );
}
