import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { PageHeader, SearchInput } from "../components/layout";
import QueryState from "../components/QueryState";
import { CompanyBadge } from "../components/ui";
import styles from "./CompanyIndex.module.css";

export default function CompanyIndex() {
  const [q, setQ] = useState("");
  const companies = useQuery({ queryKey: ["companies"], queryFn: () => api.companies() });
  const list = (companies.data ?? []).filter((c) => c.name.toLowerCase().includes(q.toLowerCase()));
  return (
    <main className="page">
      <PageHeader
        title="Companies"
        subtitle={`${companies.data?.length ?? ""} companies · sorted by number of tagged problems`}
      >
        <SearchInput id="cq" label="Search companies" value={q} onChange={setQ} width={280} autoFocus />
      </PageHeader>
      <QueryState query={companies}>
        {() => (
          <div className={styles.grid}>
            {list.map((c) => (
              <Link key={c.slug} to={`/companies/${c.slug}`} className={`card ${styles.tile}`}>
                <CompanyBadge name={c.name} size={26} />
                <span className={`ellipsis ${styles.name}`}>{c.name}</span>
                <span className="mono note">{c.count}</span>
              </Link>
            ))}
          </div>
        )}
      </QueryState>
    </main>
  );
}
