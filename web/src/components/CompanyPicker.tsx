import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "../api";
import { SearchInput } from "./layout";
import { CompanyBadge } from "./ui";

const SHOWN_COLLAPSED = 10;

export default function CompanyPicker({ value, onChange }: { value: string; onChange: (slug: string) => void }) {
  const [q, setQ] = useState("");
  const [expanded, setExpanded] = useState(false);
  const companies = useQuery({ queryKey: ["companies"], queryFn: () => api.companies() });
  const matches = (companies.data ?? []).filter((c) => c.name.toLowerCase().includes(q.toLowerCase()));
  const open = expanded || q !== "";
  const shown = open ? matches : matches.slice(0, SHOWN_COLLAPSED);
  return (
    <section className="stack">
      <div className="row spread">
        <h2 className="lbl">Company</h2>
        <span className="mono note">{companies.data?.length ?? ""}</span>
      </div>
      <SearchInput id="co-search" label="Search companies" value={q} onChange={setQ} />
      <div className={open ? "picker-list open" : "picker-list"}>
        {shown.map((c) => (
          <button
            key={c.slug}
            className={`co ${c.slug === value ? "on" : ""}`}
            aria-pressed={c.slug === value}
            onClick={() => onChange(c.slug === value ? "" : c.slug)}
          >
            <CompanyBadge name={c.name} />
            <span className="ellipsis">{c.name}</span>
            <span className="mono note">{c.count}</span>
          </button>
        ))}
      </div>
      {!q && matches.length > SHOWN_COLLAPSED && (
        <button className="btn ghost picker-toggle" onClick={() => setExpanded(!expanded)}>
          {expanded ? "Show fewer" : `Show all ${matches.length} companies`}
        </button>
      )}
    </section>
  );
}
