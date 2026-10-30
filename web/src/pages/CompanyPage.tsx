import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api, WINDOW_LABEL, type Difficulty } from "../api";
import { Meter } from "../components/layout";
import ProblemTable from "../components/ProblemTable";
import { CompanyBadge, DiffText, Pager, Segmented, WindowToggle } from "../components/ui";
import { useQueryParams } from "../hooks/useQueryParams";
import { DIFFICULTY_FILTERS, DIFFICULTY_OPTIONS, oneOf, WINDOWS } from "../lib/filters";
import styles from "./CompanyPage.module.css";

const PAGE = 25;
const DIFFICULTIES: Difficulty[] = ["Easy", "Medium", "Hard"];
const DIFF_COLOR: Record<Difficulty, string> = { Easy: "var(--easy)", Medium: "var(--med)", Hard: "var(--hard)" };
const STATUS_OPTIONS = [
  { value: "", label: "All" },
  { value: "unsolved", label: "Unsolved" },
  { value: "solved", label: "Solved" },
] as const;
type CompanyStatus = (typeof STATUS_OPTIONS)[number]["value"];

export default function CompanyPage() {
  const { slug = "" } = useParams();
  const nav = useNavigate();
  const { get, set } = useQueryParams();
  const window = oneOf(get("window"), WINDOWS, "6m");
  const status = oneOf<CompanyStatus>(get("status"), ["", "unsolved", "solved"], "");
  const difficulty = oneOf(get("difficulty"), DIFFICULTY_FILTERS, "");
  const page = Number(get("page", "1"));

  const summary = useQuery({
    queryKey: ["company", slug, window],
    queryFn: () => api.company(slug, window),
    placeholderData: keepPreviousData,
  });
  const params = { company: slug, window, status, difficulty, page, page_size: PAGE };
  const list = useQuery({
    queryKey: ["problems", params],
    queryFn: () => api.problems(params),
    placeholderData: keepPreviousData,
  });
  const s = summary.data;
  const suffix = `?company=${slug}&window=${window}`;
  const share = (n: number) => (s?.total ? n / s.total : 0);

  if (summary.isError) return <main className="page">Unknown company.</main>;
  return (
    <main className="page">
      <nav className="note text-sm">
        <Link to="/companies">Companies</Link> / {s?.name}
      </nav>
      <div className={styles.hero}>
        {s && <CompanyBadge name={s.name} size={40} />}
        <div className={styles.heroText}>
          <h1 className="title-1">{s?.name}</h1>
          <div className="note text-sm">
            {s?.total ?? "…"} problems asked{" "}
            {window === "all" ? "overall" : `in the last ${WINDOW_LABEL[window].toLowerCase()}`}
            {s && ` · ${s.windows.all} all time`}
            {s?.updated && ` · list imported ${new Date(s.updated).toLocaleDateString()}`}
          </div>
        </div>
        <WindowToggle value={window} onChange={(w) => set({ window: w })} counts={s?.windows} />
        <button
          className="btn primary lg"
          disabled={!s?.next_unsolved.length}
          onClick={() => s?.next_unsolved[0] && nav(`/problems/${s.next_unsolved[0].slug}${suffix}`)}
        >
          Practice next unsolved
        </button>
      </div>

      {s && (
        <section className={`grid ${styles.cards}`}>
          <div className="card">
            <div className="row spread">
              <h2 className="lbl">By difficulty</h2>
              <span className="note">{s.total} problems</span>
            </div>
            <div className={styles.split}>
              {DIFFICULTIES.map((d) => (
                <span key={d} style={{ width: `${share(s.by_difficulty[d]) * 100}%`, background: DIFF_COLOR[d] }} />
              ))}
            </div>
            {DIFFICULTIES.map((d) => (
              <div key={d} className={styles.line}>
                <DiffText d={d} />
                <span className="mono fg2">
                  {s.by_difficulty[d]} <span className="muted">{Math.round(share(s.by_difficulty[d]) * 100)}%</span>
                </span>
              </div>
            ))}
          </div>
          <div className="card">
            <div className="row spread">
              <h2 className="lbl">Top topics</h2>
              <span className="note">problems tagged</span>
            </div>
            {s.top_topics.map((t) => (
              <div key={t.name} className={styles.topicRow}>
                <span>{t.name}</span>
                <Meter ratio={t.count / (s.top_topics[0]?.count || 1)} />
                <span className="mono muted num">{t.count}</span>
              </div>
            ))}
          </div>
          <div className="card">
            <div className="row spread">
              <h2 className="lbl">Your progress</h2>
              <Link className="note" to="/progress">
                All companies →
              </Link>
            </div>
            <div className={styles.solved}>
              {s.solved} <span className="stat-of">/ {s.total} solved</span>
            </div>
            <Meter ratio={share(s.solved)} color="var(--easy)" />
            <div className="note">
              {s.attempted} attempted · {s.total - s.solved} left
            </div>
            <h3 className="lbl">Next unsolved, by frequency</h3>
            {s.next_unsolved.map((p) => (
              <Link key={p.slug} className={styles.link} to={`/problems/${p.slug}${suffix}`}>
                <span>
                  {p.id}. {p.title}
                </span>
                <DiffText d={p.difficulty} />
              </Link>
            ))}
            {s.next_unsolved.length === 0 && <span className="muted">All done for this window.</span>}
          </div>
        </section>
      )}

      <div className="row">
        <h2 className="title-2">Most asked</h2>
        <span className="note">
          {list.data?.total ?? ""} problems · {WINDOW_LABEL[window]} · sorted by frequency
        </span>
        <div className="spacer" />
        <Segmented label="Status" options={STATUS_OPTIONS} value={status} onChange={(v) => set({ status: v })} />
        <Segmented
          label="Difficulty"
          options={DIFFICULTY_OPTIONS}
          value={difficulty}
          onChange={(v) => set({ difficulty: v })}
        />
      </div>
      <ProblemTable rows={list.data?.items ?? []} showFreq linkSuffix={suffix} />
      {list.data && <Pager page={page} total={list.data.total} size={PAGE} onPage={(p) => set({ page: String(p) })} />}
    </main>
  );
}
