import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { ICONS } from "../lib/icons";
import { Link } from "react-router-dom";
import { useQueryParams } from "../hooks/useQueryParams";
import { api, type Window } from "../api";
import CompanyPicker from "../components/CompanyPicker";
import ProblemTable from "../components/ProblemTable";
import { CompanyBadge, Icon, Pager, WindowToggle } from "../components/ui";

const PAGE = 50;

export default function ProblemList() {
  const { get, set } = useQueryParams();
  const company = get("company");
  const window = get("window", "6m") as Window;
  const page = Number(get("page", "1"));
  const tags = get("tags").split(",").filter(Boolean);

  const params = {
    q: get("q"),
    difficulty: get("difficulty"),
    status: get("status"),
    tags: get("tags"),
    company,
    window,
    page,
    page_size: PAGE,
  };
  const list = useQuery({
    queryKey: ["problems", params],
    queryFn: () => api.problems(params),
    placeholderData: keepPreviousData,
  });
  const allTags = useQuery({ queryKey: ["tags"], queryFn: api.tags });
  const companies = useQuery({ queryKey: ["companies"], queryFn: () => api.companies() });
  const companyName = companies.data?.find((c) => c.slug === company)?.name ?? company;
  const counts = list.data?.counts;
  const solved = counts ? counts.easy[0] + counts.medium[0] + counts.hard[0] : 0;
  const total = counts ? counts.easy[1] + counts.medium[1] + counts.hard[1] : 0;

  return (
    <div style={{ display: "flex", flex: 1, minHeight: 0, flexWrap: "wrap" }}>
      <aside
        style={{
          width: 260,
          flex: "0 0 260px",
          borderRight: "1px solid var(--line)",
          padding: 16,
          display: "flex",
          flexDirection: "column",
          gap: 20,
          background: "var(--panel)",
        }}
      >
        <div style={{ position: "relative" }}>
          <label className="sr" htmlFor="search">
            Search problems
          </label>
          <span style={{ position: "absolute", left: 10, top: 8, color: "var(--fg3)" }}>
            <Icon d={ICONS.search} />
          </span>
          <input
            id="search"
            className="inp icon"
            placeholder="Search problems"
            defaultValue={get("q")}
            onChange={(e) => set({ q: e.target.value })}
          />
        </div>
        <CompanyPicker value={company} onChange={(c) => set({ company: c })} />
        <section style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          <h2 className="lbl">Difficulty</h2>
          <div className="seg" role="group" aria-label="Difficulty">
            {["", "Easy", "Medium", "Hard"].map((d) => (
              <button key={d} className={get("difficulty") === d ? "on" : ""} onClick={() => set({ difficulty: d })}>
                {d || "All"}
              </button>
            ))}
          </div>
        </section>
        <section style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          <h2 className="lbl">Status</h2>
          <div className="seg" role="group" aria-label="Status">
            {[
              ["", "All"],
              ["solved", "Solved"],
              ["attempted", "Attempted"],
              ["todo", "Todo"],
            ].map(([v, l]) => (
              <button key={v} className={get("status") === v ? "on" : ""} onClick={() => set({ status: v })}>
                {l}
              </button>
            ))}
          </div>
        </section>
        <section style={{ display: "flex", flexDirection: "column", gap: 2 }}>
          <div style={{ display: "flex", justifyContent: "space-between" }}>
            <h2 className="lbl">Topics</h2>
            <span className="muted" style={{ fontSize: 11 }}>
              match any
            </span>
          </div>
          {(allTags.data ?? []).slice(0, 18).map((t) => (
            <label key={t.name} className="chk">
              <input
                type="checkbox"
                checked={tags.includes(t.name)}
                onChange={(e) =>
                  set({ tags: (e.target.checked ? [...tags, t.name] : tags.filter((x) => x !== t.name)).join(",") })
                }
              />
              <span style={{ flex: 1 }}>{t.name}</span>
              <span className="mono muted" style={{ fontSize: 11 }}>
                {t.count}
              </span>
            </label>
          ))}
        </section>
      </aside>

      <main
        style={{
          flex: "1 1 600px",
          minWidth: 0,
          padding: "20px 24px 32px",
          display: "flex",
          flexDirection: "column",
          gap: 14,
        }}
      >
        {counts && (
          <div style={{ display: "flex", alignItems: "center", gap: 18, flexWrap: "wrap" }}>
            <div>
              <span style={{ fontSize: 18, fontWeight: 600 }}>{solved.toLocaleString()}</span>
              <span className="muted"> / {total.toLocaleString()} solved</span>
            </div>
            {(["easy", "medium", "hard"] as const).map((k) => (
              <span key={k} style={{ fontSize: 12.5 }}>
                <span className={`diff ${k[0].toUpperCase() + k.slice(1)}`}>{k[0].toUpperCase() + k.slice(1)}</span>{" "}
                <span className="mono" style={{ color: "var(--fg2)" }}>
                  {counts[k][0]} / {counts[k][1].toLocaleString()}
                </span>
              </span>
            ))}
          </div>
        )}

        {company && (
          <div
            className="card"
            style={{ flexDirection: "row", alignItems: "center", gap: 12, padding: "12px 14px", flexWrap: "wrap" }}
          >
            <CompanyBadge name={companyName} size={28} />
            <div style={{ flex: 1, minWidth: 160 }}>
              <div style={{ fontWeight: 600, fontSize: 14 }}>{companyName}</div>
              <div className="muted" style={{ fontSize: 12 }}>
                {list.data?.total ?? "…"} problems · sorted by frequency
              </div>
            </div>
            <WindowToggle value={window} onChange={(w) => set({ window: w })} />
            <Link className="btn" to={`/companies/${company}?window=${window}`}>
              Company page →
            </Link>
            <button className="btn ghost" onClick={() => set({ company: "" })}>
              Clear
            </button>
          </div>
        )}

        <ProblemTable
          rows={list.data?.items ?? []}
          showFreq={!!company}
          linkSuffix={company ? `?company=${company}&window=${window}` : ""}
        />
        {list.data && (
          <Pager page={page} total={list.data.total} size={PAGE} onPage={(p) => set({ page: String(p) })} />
        )}
      </main>
    </div>
  );
}
