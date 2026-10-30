import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useQueryParams } from "../hooks/useQueryParams";
import { DIFFICULTY_FILTERS, oneOf, STATUS_FILTERS, WINDOWS } from "../lib/filters";
import { api, WINDOW_LABEL, type Difficulty } from "../api";
import ProblemTable from "../components/ProblemTable";
import { CompanyBadge, DiffText, Pager, WindowToggle } from "../components/ui";

const PAGE = 25;
const DIFF_VAR: Record<Difficulty, string> = { Easy: "var(--easy)", Medium: "var(--med)", Hard: "var(--hard)" };

export default function CompanyPage() {
  const { slug = "" } = useParams();
  const nav = useNavigate();
  const { get, set } = useQueryParams();
  const window = oneOf(get("window"), WINDOWS, "6m");
  const status = oneOf(get("status"), STATUS_FILTERS, "");
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

  if (summary.isError) return <main style={{ padding: 24 }}>Unknown company.</main>;
  return (
    <main
      style={{
        width: "100%",
        maxWidth: 1280,
        margin: "0 auto",
        padding: "24px 24px 40px",
        display: "flex",
        flexDirection: "column",
        gap: 16,
      }}
    >
      <nav className="muted" style={{ fontSize: 12.5 }}>
        <Link to="/companies">Companies</Link> / {s?.name}
      </nav>
      <div style={{ display: "flex", alignItems: "center", gap: 14, flexWrap: "wrap" }}>
        {s && <CompanyBadge name={s.name} size={40} />}
        <div style={{ flex: 1, minWidth: 220 }}>
          <h1 style={{ margin: 0, fontSize: 22, fontWeight: 600 }}>{s?.name}</h1>
          <div className="muted" style={{ fontSize: 12.5 }}>
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
        <section
          style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(min(300px, 100%), 1fr))", gap: 12 }}
        >
          <div className="card">
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <h2 className="lbl">By difficulty</h2>
              <span className="muted" style={{ fontSize: 12 }}>
                {s.total} problems
              </span>
            </div>
            <div
              style={{ display: "flex", height: 10, borderRadius: 5, overflow: "hidden", background: "var(--line)" }}
            >
              {(["Easy", "Medium", "Hard"] as Difficulty[]).map((d) => (
                <span
                  key={d}
                  style={{ width: `${s.total ? (s.by_difficulty[d] / s.total) * 100 : 0}%`, background: DIFF_VAR[d] }}
                />
              ))}
            </div>
            {(["Easy", "Medium", "Hard"] as Difficulty[]).map((d) => (
              <div key={d} style={{ display: "flex", justifyContent: "space-between", fontSize: 12.5 }}>
                <DiffText d={d} />
                <span className="mono" style={{ color: "var(--fg2)" }}>
                  {s.by_difficulty[d]}{" "}
                  <span className="muted">{s.total ? Math.round((s.by_difficulty[d] / s.total) * 100) : 0}%</span>
                </span>
              </div>
            ))}
          </div>
          <div className="card">
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <h2 className="lbl">Top topics</h2>
              <span className="muted" style={{ fontSize: 12 }}>
                problems tagged
              </span>
            </div>
            {s.top_topics.map((t) => (
              <div
                key={t.name}
                style={{
                  display: "grid",
                  gridTemplateColumns: "130px 1fr 36px",
                  gap: 10,
                  alignItems: "center",
                  fontSize: 12.5,
                }}
              >
                <span>{t.name}</span>
                <div className="bar">
                  <span style={{ width: `${(t.count / (s.top_topics[0]?.count || 1)) * 100}%` }} />
                </div>
                <span className="mono muted" style={{ textAlign: "right" }}>
                  {t.count}
                </span>
              </div>
            ))}
          </div>
          <div className="card">
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <h2 className="lbl">Your progress</h2>
              <Link to="/progress" style={{ fontSize: 12 }}>
                All companies →
              </Link>
            </div>
            <div style={{ fontSize: 26, fontWeight: 600 }}>
              {s.solved}{" "}
              <span className="muted" style={{ fontSize: 14, fontWeight: 400 }}>
                / {s.total} solved
              </span>
            </div>
            <div className="bar">
              <span style={{ width: `${s.total ? (s.solved / s.total) * 100 : 0}%`, background: "var(--easy)" }} />
            </div>
            <div className="muted" style={{ fontSize: 12 }}>
              {s.attempted} attempted · {s.total - s.solved} left
            </div>
            <h3 className="lbl" style={{ marginTop: 4 }}>
              Next unsolved, by frequency
            </h3>
            {s.next_unsolved.map((p) => (
              <Link
                key={p.slug}
                to={`/problems/${p.slug}${suffix}`}
                style={{ display: "flex", justifyContent: "space-between", color: "var(--fg)", fontSize: 12.5 }}
              >
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

      <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap", marginTop: 4 }}>
        <h2 style={{ margin: 0, fontSize: 15, fontWeight: 600 }}>Most asked</h2>
        <span className="muted" style={{ fontSize: 12 }}>
          {list.data?.total ?? ""} problems · {WINDOW_LABEL[window]} · sorted by frequency
        </span>
        <div style={{ flex: 1 }} />
        <div className="seg" role="group" aria-label="Status">
          {[
            ["", "All"],
            ["unsolved", "Unsolved"],
            ["solved", "Solved"],
          ].map(([v, l]) => (
            <button key={v} className={status === v ? "on" : ""} onClick={() => set({ status: v })}>
              {l}
            </button>
          ))}
        </div>
        <div className="seg" role="group" aria-label="Difficulty">
          {["", "Easy", "Medium", "Hard"].map((d) => (
            <button key={d} className={difficulty === d ? "on" : ""} onClick={() => set({ difficulty: d })}>
              {d || "All"}
            </button>
          ))}
        </div>
      </div>
      <ProblemTable rows={list.data?.items ?? []} showFreq linkSuffix={suffix} />
      {list.data && <Pager page={page} total={list.data.total} size={PAGE} onPage={(p) => set({ page: String(p) })} />}
    </main>
  );
}
