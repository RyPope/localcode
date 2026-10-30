"""Problem catalogue: listing, detail, tags and reference solutions."""

import json
import sqlite3

from localcode.db import content_session
from localcode.services.errors import bad_request, not_found
from localcode.services.sql import DIFFICULTIES, STATUS, WINDOWS

KOTLIN_FALLBACK_NOTE = "No Kotlin reference yet — showing Java."
STATUS_FILTERS = {
    "solved": "status = 'solved'",
    "attempted": "status = 'attempted'",
    "todo": "status = 'todo'",
    "unsolved": "status != 'solved'",
}
SORTS = {
    "id": "frontend_id",
    "frequency": "frequency desc",
    "acceptance": "acceptance desc",
    "difficulty": "case difficulty when 'Easy' then 0 when 'Medium' then 1 else 2 end",
}


def load_problem(con: sqlite3.Connection, slug: str) -> sqlite3.Row:
    row = con.execute(f"select p.*, {STATUS} as status from problems p where p.slug = ?", (slug,)).fetchone()
    if not row:
        raise not_found(f"problem {slug!r}")
    return row


def content_version(con: sqlite3.Connection) -> str:
    """Identifies the imported content; changes on every import."""
    row = con.execute("select value from meta where key = 'imported_at'").fetchone()
    return row[0] if row else ""


def _difficulty_counts(con: sqlite3.Connection) -> dict[str, list[int]]:
    counts = {d.lower(): [0, 0] for d in DIFFICULTIES}
    for diff, solved, n in con.execute(
        f"select difficulty, {STATUS} = 'solved', count(*) from problems p group by 1, 2"
    ):
        if diff in DIFFICULTIES:
            counts[diff.lower()][1] += n
            if solved:
                counts[diff.lower()][0] += n
    return counts


def list_problems(
    q: str = "",
    difficulty: str = "",
    status: str = "",
    tags: str = "",
    company: str = "",
    window: str = "6m",
    sort: str = "",
    page: int = 1,
    page_size: int = 50,
) -> dict:
    where: list[str] = []
    args: list = []
    join, freq = "", "null"
    if company:
        if window not in WINDOWS:
            raise bad_request(f"window must be one of {', '.join(WINDOWS)}")
        join = "join company_problems cp on cp.slug = p.slug and cp.company = ? and cp.window = ?"
        args += [company, window]
        freq = "cp.frequency"
    if q.strip():
        if q.strip().isdigit():
            where.append("p.frontend_id = ?")
            args.append(int(q))
        else:
            where.append("p.title like ?")
            args.append(f"%{q.strip()}%")
    if difficulty:
        where.append("p.difficulty = ?")
        args.append(difficulty)
    tag_list = [t for t in tags.split(",") if t]
    if tag_list:
        where.append(
            "(" + " or ".join(["exists(select 1 from json_each(p.tags) where value = ?)"] * len(tag_list)) + ")"
        )
        args += tag_list
    if status and status not in STATUS_FILTERS:
        raise bad_request(f"status must be one of {', '.join(STATUS_FILTERS)}")

    inner = (
        f"select p.slug, p.frontend_id, p.title, p.difficulty, p.acceptance, p.tags, p.has_tests, "
        f"{freq} as frequency, {STATUS} as status from problems p {join}"
        + (" where " + " and ".join(where) if where else "")
    )
    query = f"select * from ({inner})" + (f" where {STATUS_FILTERS[status]}" if status else "")
    order = SORTS.get(sort or ("frequency" if company else "id"), SORTS["id"])
    with content_session() as con:
        total = con.execute(f"select count(*) from ({query})", args).fetchone()[0]
        rows = con.execute(
            f"{query} order by {order}, frontend_id limit ? offset ?",
            [*args, page_size, (max(page, 1) - 1) * page_size],
        ).fetchall()
        counts = _difficulty_counts(con)
    return {
        "total": total,
        "counts": counts,
        "items": [
            {
                "slug": r["slug"],
                "id": r["frontend_id"],
                "title": r["title"],
                "difficulty": r["difficulty"],
                "acceptance": r["acceptance"],
                "tags": json.loads(r["tags"]),
                "frequency": r["frequency"],
                "status": r["status"],
                "has_tests": bool(r["has_tests"]),
            }
            for r in rows
        ],
    }


def all_tags() -> list[dict]:
    with content_session() as con:
        rows = con.execute("select value, count(*) from problems, json_each(problems.tags) group by 1 order by 2 desc")
        return [{"name": name, "count": n} for name, n in rows]


def problem_detail(slug: str) -> dict:
    with content_session() as con:
        p = load_problem(con, slug)
        starters = dict(con.execute("select lang, code from starters where slug = ?", (slug,)).fetchall())
        companies = [
            dict(r)
            for r in con.execute(
                # Larger companies first: raw frequency is relative to each company's own list.
                "select c.slug, c.name, cp.frequency from company_problems cp join companies c on c.slug = cp.company "
                "where cp.slug = ? and cp.window = 'all' order by (select count(*) from company_problems x "
                "where x.company = c.slug and x.window = 'all') desc limit 30",
                (slug,),
            )
        ]
        neighbours = con.execute(
            "select (select slug from problems where frontend_id < ? order by frontend_id desc limit 1), "
            "(select slug from problems where frontend_id > ? order by frontend_id limit 1)",
            (p["frontend_id"], p["frontend_id"]),
        ).fetchone()
        tests = con.execute("select json_array_length(cases) from tests where slug = ?", (slug,)).fetchone()
    return {
        "slug": p["slug"],
        "id": p["frontend_id"],
        "title": p["title"],
        "difficulty": p["difficulty"],
        "tags": json.loads(p["tags"]),
        "acceptance": p["acceptance"],
        "description_html": p["description_html"],
        "params": json.loads(p["params"]) if p["params"] else [],
        "examples": json.loads(p["examples"] or "[]"),
        "has_tests": bool(p["has_tests"]),
        "test_count": tests[0] if tests else 0,
        "langs": json.loads(p["langs"]),
        "starters": starters,
        "companies": companies,
        "status": p["status"],
        "prev": neighbours[0],
        "next": neighbours[1],
    }


def solutions(slug: str) -> list[dict]:
    """Reference solutions; Kotlin falls back to Java (doocs has few Kotlin solutions)."""
    with content_session() as con:
        load_problem(con, slug)
        rows = con.execute(
            "select title, explanation_md, code from solutions where slug = ? order by idx", (slug,)
        ).fetchall()
    out = []
    for r in rows:
        code, notes = json.loads(r["code"]), {}
        if "kotlin" not in code and "java" in code:
            code["kotlin"] = code["java"]
            notes["kotlin"] = KOTLIN_FALLBACK_NOTE
        out.append({"title": r["title"], "explanation_md": r["explanation_md"], "code": code, "notes": notes})
    return out
