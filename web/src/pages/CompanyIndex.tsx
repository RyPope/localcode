import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { CompanyBadge, Icon, ICONS } from "../components/ui";

export default function CompanyIndex() {
  const [q, setQ] = useState("");
  const companies = useQuery({ queryKey: ["companies"], queryFn: () => api.companies() });
  const list = (companies.data ?? []).filter((c) => c.name.toLowerCase().includes(q.toLowerCase()));
  return (
    <main style={{ width: "100%", maxWidth: 1280, margin: "0 auto", padding: "24px 24px 40px", display: "flex", flexDirection: "column", gap: 16 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
        <h1 style={{ margin: 0, fontSize: 22, fontWeight: 600 }}>Companies</h1>
        <span className="muted">{companies.data?.length ?? ""} companies · sorted by number of tagged problems</span>
        <div style={{ flex: 1 }} />
        <div style={{ position: "relative", width: 280 }}>
          <label className="sr" htmlFor="cq">Search companies</label>
          <span style={{ position: "absolute", left: 10, top: 8, color: "var(--fg3)" }}><Icon d={ICONS.search} /></span>
          <input id="cq" className="inp icon" placeholder="Search companies" value={q} onChange={(e) => setQ(e.target.value)} autoFocus />
        </div>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))", gap: 8 }}>
        {list.map((c) => (
          <Link key={c.slug} to={`/companies/${c.slug}`} className="card"
            style={{ flexDirection: "row", alignItems: "center", gap: 10, padding: "10px 12px", color: "var(--fg)" }}>
            <CompanyBadge name={c.name} size={26} />
            <span style={{ flex: 1, fontWeight: 500, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{c.name}</span>
            <span className="mono muted" style={{ fontSize: 12 }}>{c.count}</span>
          </Link>
        ))}
      </div>
    </main>
  );
}
