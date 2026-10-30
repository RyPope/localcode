"""Company lists and per-company summaries."""

import json
from collections import Counter

from localcode.db import content_session
from localcode.services.errors import bad_request, not_found
from localcode.services.models import Company, CompanySummary
from localcode.services.sql import DIFFICULTIES, STATUS, WINDOWS, contains


def list_companies(q: str = "") -> list[Company]:
    with content_session() as con:
        rows = con.execute(
            "select c.slug, c.name, count(cp.slug) from companies c left join company_problems cp "
            "on cp.company = c.slug and cp.window = 'all' where c.name like ? escape '\\' "
            "group by c.slug order by 3 desc, c.name",
            (contains(q),),
        )
        return [{"slug": slug, "name": name, "count": n} for slug, name, n in rows]


def company_summary(slug: str, window: str = "6m") -> CompanySummary:
    if window not in WINDOWS:
        raise bad_request(f"window must be one of {', '.join(WINDOWS)}")
    with content_session() as con:
        company = con.execute("select name from companies where slug = ?", (slug,)).fetchone()
        if not company:
            raise not_found(f"company {slug!r}")
        windows = dict.fromkeys(WINDOWS, 0)
        windows.update(
            con.execute(
                "select window, count(*) from company_problems where company = ? group by 1", (slug,)
            ).fetchall()
        )
        rows = con.execute(
            f"select p.slug, p.frontend_id, p.title, p.difficulty, p.tags, {STATUS} as status "
            f"from company_problems cp join problems p on p.slug = cp.slug "
            f"where cp.company = ? and cp.window = ? order by cp.frequency desc",
            (slug, window),
        ).fetchall()
        updated = con.execute("select value from meta where key = 'imported_at'").fetchone()

    by_difficulty = dict.fromkeys(DIFFICULTIES, 0)
    topics: Counter[str] = Counter()
    for r in rows:
        if r["difficulty"] in by_difficulty:
            by_difficulty[r["difficulty"]] += 1
        topics.update(json.loads(r["tags"]))
    unsolved = [r for r in rows if r["status"] != "solved"]
    return {
        "slug": slug,
        "name": company["name"],
        "window": window,
        "total": len(rows),
        "windows": windows,
        "by_difficulty": by_difficulty,
        "top_topics": [{"name": n, "count": k} for n, k in topics.most_common(8)],
        "solved": sum(r["status"] == "solved" for r in rows),
        "attempted": sum(r["status"] == "attempted" for r in rows),
        "next_unsolved": [
            {"slug": r["slug"], "id": r["frontend_id"], "title": r["title"], "difficulty": r["difficulty"]}
            for r in unsolved[:3]
        ],
        "updated": updated[0] if updated else None,
    }
