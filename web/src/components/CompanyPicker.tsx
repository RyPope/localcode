import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "../api";
import { CompanyBadge, Icon, ICONS } from "./ui";

export default function CompanyPicker({ value, onChange }: { value: string; onChange: (slug: string) => void }) {
  const [q, setQ] = useState("");
  const [all, setAll] = useState(false);
  const companies = useQuery({ queryKey: ["companies"], queryFn: () => api.companies() });
  const list = (companies.data ?? []).filter((c) => c.name.toLowerCase().includes(q.toLowerCase()));
  const shown = all || q ? list : list.slice(0, 10);
  return (
    <section style={{ display: "flex", flexDirection: "column", gap: 6 }}>
      <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between" }}>
        <h2 className="lbl">Company</h2>
        <span className="muted mono" style={{ fontSize: 11 }}>{companies.data?.length ?? ""}</span>
      </div>
      <div style={{ position: "relative" }}>
        <label className="sr" htmlFor="co-search">Search companies</label>
        <span style={{ position: "absolute", left: 10, top: 8, color: "var(--fg3)" }}><Icon d={ICONS.search} /></span>
        <input id="co-search" className="inp icon" placeholder="Search companies" value={q} onChange={(e) => setQ(e.target.value)} />
      </div>
      <div style={{ display: "flex", flexDirection: "column", maxHeight: all || q ? 320 : undefined, overflowY: "auto" }}>
        {shown.map((c) => (
          <button key={c.slug} className={`co ${c.slug === value ? "on" : ""}`} aria-pressed={c.slug === value}
            onClick={() => onChange(c.slug === value ? "" : c.slug)}>
            <CompanyBadge name={c.name} />
            <span style={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{c.name}</span>
            <span className="mono muted" style={{ fontSize: 11 }}>{c.count}</span>
          </button>
        ))}
      </div>
      {!q && list.length > 10 && (
        <button className="btn ghost" style={{ alignSelf: "flex-start" }} onClick={() => setAll(!all)}>
          {all ? "Show fewer" : `Show all ${list.length} companies`}
        </button>
      )}
    </section>
  );
}
