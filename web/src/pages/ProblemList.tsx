import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import CompanyPicker from "../components/CompanyPicker";
import { SearchInput } from "../components/layout";
import ProblemTable from "../components/ProblemTable";
import { CompanyBadge, Icon, Pager, Segmented, WindowToggle } from "../components/ui";
import { useQueryParams } from "../hooks/useQueryParams";
import { ICONS } from "../lib/icons";
import { DIFFICULTY_FILTERS, DIFFICULTY_OPTIONS, oneOf, STATUS_FILTERS, WINDOWS } from "../lib/filters";
import styles from "./ProblemList.module.css";

const PAGE = 50;
const TOPICS_SHOWN = 18;
const STATUS_OPTIONS = [
  { value: "", label: "All" },
  { value: "solved", label: "Solved" },
  { value: "attempted", label: "Attempted" },
  { value: "todo", label: "Todo" },
] as const;
const DIFFICULTY_KEYS = [
  ["easy", "Easy"],
  ["medium", "Medium"],
  ["hard", "Hard"],
] as const;

export default function ProblemList() {
  const { get, set } = useQueryParams();
  const company = get("company");
  const window = oneOf(get("window"), WINDOWS, "6m");
  const difficulty = oneOf(get("difficulty"), DIFFICULTY_FILTERS, "");
  const status = oneOf(get("status"), STATUS_FILTERS, "");
  const page = Number(get("page", "1"));
  const tags = get("tags").split(",").filter(Boolean);

  const params = { q: get("q"), difficulty, status, tags: get("tags"), company, window, page, page_size: PAGE };
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
  const activeFilters = [get("q"), company, difficulty, status].filter(Boolean).length + tags.length;
  const [filtersOpen, setFiltersOpen] = useState(false);
  const toggleTag = (name: string, on: boolean) =>
    set({ tags: (on ? [...tags, name] : tags.filter((t) => t !== name)).join(",") });

  return (
    <div className={styles.layout}>
      <button
        className={`btn ${styles.filtersToggle}`}
        aria-expanded={filtersOpen}
        aria-controls="filters"
        onClick={() => setFiltersOpen((open) => !open)}
      >
        <Icon d={ICONS.filter} />
        {filtersOpen ? "Hide filters" : "Filters"}
        {activeFilters > 0 && <span className="mono muted">{activeFilters}</span>}
      </button>
      <aside id="filters" className={`${styles.rail} ${filtersOpen ? styles.open : ""}`}>
        <SearchInput id="search" label="Search problems" defaultValue={get("q")} onChange={(q) => set({ q })} />
        <CompanyPicker value={company} onChange={(c) => set({ company: c })} />
        <section className="stack">
          <h2 className="lbl">Difficulty</h2>
          <Segmented
            label="Difficulty"
            options={DIFFICULTY_OPTIONS}
            value={difficulty}
            onChange={(v) => set({ difficulty: v })}
          />
        </section>
        <section className="stack">
          <h2 className="lbl">Status</h2>
          <Segmented
            label="Status"
            options={STATUS_OPTIONS}
            value={oneOf(status, ["", "solved", "attempted", "todo"], "")}
            onChange={(v) => set({ status: v })}
          />
        </section>
        <section className={styles.topics}>
          <div className="row spread">
            <h2 className="lbl">Topics</h2>
            <span className="note">match any</span>
          </div>
          {(allTags.data ?? []).slice(0, TOPICS_SHOWN).map((t) => (
            <label key={t.name} className="chk">
              <input
                type="checkbox"
                checked={tags.includes(t.name)}
                onChange={(e) => toggleTag(t.name, e.target.checked)}
              />
              <span className={styles.topicName}>{t.name}</span>
              <span className="mono muted text-xs">{t.count}</span>
            </label>
          ))}
        </section>
      </aside>

      <main className={styles.main}>
        {counts && (
          <div className={styles.summary}>
            <div>
              <span className={styles.solved}>{solved.toLocaleString()}</span>
              <span className="muted"> / {total.toLocaleString()} solved</span>
            </div>
            {DIFFICULTY_KEYS.map(([key, label]) => (
              <span key={key} className="text-sm">
                <span className={`diff ${label}`}>{label}</span>{" "}
                <span className="mono fg2">
                  {counts[key][0]} / {counts[key][1].toLocaleString()}
                </span>
              </span>
            ))}
          </div>
        )}

        {company && (
          <div className={`card ${styles.companyBar}`}>
            <CompanyBadge name={companyName} size={28} />
            <div className={styles.companyText}>
              <div className="title-3">{companyName}</div>
              <div className="note">{list.data?.total ?? "…"} problems · sorted by frequency</div>
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
