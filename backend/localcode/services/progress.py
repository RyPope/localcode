"""The user's own data: drafts, submissions, statistics and export."""

import json
from collections import Counter, defaultdict
from datetime import UTC, date, datetime, timedelta

from localcode.db import content_session, user_session
from localcode.services.errors import bad_request
from localcode.services.models import Export, Stats, Submission
from localcode.services.sql import DIFFICULTIES, LANGS

STATS_WEEKS = 26
STATS_TOPICS = 12
STATS_COMPANIES = 8


def now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def get_draft(slug: str, lang: str) -> str | None:
    with user_session() as u:
        row = u.execute("select code from drafts where slug = ? and lang = ?", (slug, lang)).fetchone()
    return row[0] if row else None


def save_draft(slug: str, lang: str, code: str) -> None:
    if lang not in LANGS:
        raise bad_request(f"Unknown language {lang!r}")
    with user_session() as u:
        u.execute(
            "insert into drafts (slug, lang, code, updated_at) values (?,?,?,?) on conflict(slug, lang) do update set "
            "code = excluded.code, updated_at = excluded.updated_at",
            (slug, lang, code, now_iso()),
        )


def record_submission(slug: str, lang: str, code: str, grade: dict) -> int:
    with user_session() as u:
        cur = u.execute(
            "insert into submissions "
            "(slug, lang, code, verdict, passed, total, runtime_ms, memory_kb, failing, created_at) "
            "values (?,?,?,?,?,?,?,?,?,?)",
            (
                slug,
                lang,
                code,
                grade["verdict"],
                grade["passed"],
                grade["total"],
                grade["runtime_ms"],
                grade["memory_kb"],
                json.dumps(grade["failing"]) if grade["failing"] else None,
                now_iso(),
            ),
        )
        return int(cur.lastrowid)


def list_submissions(slug: str) -> list[Submission]:
    with user_session() as u:
        rows = u.execute("select * from submissions where slug = ? order by id desc", (slug,)).fetchall()
    return [{**dict(r), "failing": json.loads(r["failing"]) if r["failing"] else None} for r in rows]


def _week_start(d: date) -> date:
    return d - timedelta(days=d.weekday())


def stats() -> Stats:
    """Totals by difficulty, first-accepted problems per week, coverage by topic and company, and every
    solved problem."""
    with content_session() as con:
        firsts = con.execute(
            "select s.slug, min(s.created_at) as at, p.frontend_id, p.title, p.difficulty, p.tags, "
            "json_group_array(distinct s.lang) as langs from u.submissions s "
            "join problems p on p.slug = s.slug where s.verdict = 'Accepted' group by s.slug order by at desc"
        ).fetchall()
        difficulty_totals = dict(con.execute("select difficulty, count(*) from problems group by 1").fetchall())
        topic_totals = Counter(
            dict(con.execute("select value, count(*) from problems, json_each(problems.tags) group by 1").fetchall())
        )
        solved = [r["slug"] for r in firsts]
        by_company = []
        if solved:
            marks = ",".join("?" * len(solved))
            by_company = [
                {"slug": s, "name": n, "solved": k, "total": t}
                for s, n, k, t in con.execute(
                    f"select c.slug, c.name, sum(cp.slug in ({marks})), count(*) from company_problems cp "
                    f"join companies c on c.slug = cp.company where cp.window = '6m' group by c.slug "
                    f"order by 3 desc, 4 desc limit {STATS_COMPANIES}",
                    solved,
                )
            ]
        since = con.execute("select min(created_at) from u.submissions").fetchone()[0]

    totals = {d.lower(): [0, difficulty_totals.get(d, 0)] for d in DIFFICULTIES}
    weeks: dict[str, dict[str, int]] = defaultdict(lambda: {"easy": 0, "medium": 0, "hard": 0})
    topic_solved: Counter[str] = Counter()
    for r in firsts:
        key = r["difficulty"].lower()
        weeks[_week_start(datetime.fromisoformat(r["at"]).date()).isoformat()][key] += 1
        totals[key][0] += 1
        topic_solved.update(json.loads(r["tags"]))
    first_week = _week_start(date.today()) - timedelta(weeks=STATS_WEEKS - 1)
    series = []
    for i in range(STATS_WEEKS):
        wk = (first_week + timedelta(weeks=i)).isoformat()
        series.append({"week": wk, **weeks.get(wk, {"easy": 0, "medium": 0, "hard": 0})})
    return {
        "since": since,
        "totals": totals,
        "solved_by_week": series,
        "by_topic": [
            {"name": n, "solved": topic_solved[n], "total": t} for n, t in topic_totals.most_common(STATS_TOPICS)
        ],
        "by_company": by_company,
        "solved": [
            {
                "slug": r["slug"],
                "id": r["frontend_id"],
                "title": r["title"],
                "difficulty": r["difficulty"],
                "first_accepted_at": r["at"],
                "langs": sorted(json.loads(r["langs"])),
            }
            for r in firsts
        ],
    }


def export() -> Export:
    with user_session() as u:
        return {
            "exported_at": now_iso(),
            "drafts": [dict(r) for r in u.execute("select * from drafts")],
            "submissions": [dict(r) for r in u.execute("select * from submissions")],
        }
