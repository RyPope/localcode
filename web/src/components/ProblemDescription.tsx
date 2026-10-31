import { Link } from "react-router-dom";
import type { ProblemDetail } from "../api";
import { pct } from "../lib/format";
import { problemLabel } from "../lib/labels";
import styles from "./ProblemDescription.module.css";
import { CompanyBadge, Html } from "./ui";

const COMPANIES_SHOWN = 8;

export default function ProblemDescription({ problem: p }: { problem: ProblemDetail }) {
  return (
    <article className={styles.article}>
      <h1 className={styles.title}>{problemLabel(p)}</h1>
      <div className={styles.chips}>
        <span className={`dpill ${p.difficulty}`}>{p.difficulty}</span>
        {p.local && (
          <span className="tag local" title="From this repo's content/ folder">
            local
          </span>
        )}
        {p.status === "solved" && <span className={`tag ${styles.solved}`}>Solved</span>}
        {p.status === "attempted" && <span className={`tag ${styles.attempted}`}>Attempted</span>}
        <span className="note">Acceptance {pct(p.acceptance)}</span>
      </div>
      <div className={styles.chips}>
        {p.tags.map((t) => (
          <Link key={t} className="tag" to={`/?tags=${encodeURIComponent(t)}`}>
            {t}
          </Link>
        ))}
      </div>
      {p.companies.length > 0 && (
        <div className={styles.chips}>
          <span className={`lbl ${styles.askedBy}`}>Asked by</span>
          {p.companies.slice(0, COMPANIES_SHOWN).map((c) => (
            <Link key={c.slug} className={`tag ${styles.company}`} to={`/companies/${c.slug}`}>
              <CompanyBadge name={c.name} size={14} />
              {c.name}
            </Link>
          ))}
          {p.companies.length > COMPANIES_SHOWN && (
            <span className="note">+{p.companies.length - COMPANIES_SHOWN} more</span>
          )}
        </div>
      )}
      <Html html={p.description_html} />
      <footer className={styles.credits}>
        Statement via doocs/leetcode (CC BY-SA 4.0) · tests via LeetCodeDataset (Apache-2.0)
      </footer>
    </article>
  );
}
