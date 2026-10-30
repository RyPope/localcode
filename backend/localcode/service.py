"""Application logic: problem queries, Run/Submit judging, drafts, submissions and stats.

`runner` arguments are callables taking a runner request dict and returning a runner result dict.
"""
import json
import sqlite3
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from typing import Any, Callable

from localcode import config, db
from localcode.compare import judge
from localcode.kwargs import parse_kwargs

Runner = Callable[[dict], dict]
LANGS = ("python", "java", "cpp", "kotlin")
WINDOWS = ("30d", "3m", "6m", "older", "all")
KOTLIN_FALLBACK_NOTE = "No Kotlin reference yet — showing Java."
_MEMORY_MARKERS = ("MemoryError", "OutOfMemoryError", "bad_alloc")
_SIGNALS = {-11: "Segmentation fault (SIGSEGV)", -6: "Aborted (SIGABRT)", -8: "Floating point exception (SIGFPE)",
            -7: "Bus error (SIGBUS)"}
_expected_cache: dict[tuple[str, str], Any] = {}


class ServiceError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


def _conn() -> sqlite3.Connection:
    """Content connection with user.db attached as `u` (opened per call: imports swap content.db)."""
    db.connect_user().close()
    con = db.connect_content()
    con.execute("attach database ? as u", (str(db.USER_DB),))
    return con


_STATUS_SQL = """case
  when exists(select 1 from u.submissions s where s.slug = p.slug and s.verdict = 'Accepted') then 'solved'
  when exists(select 1 from u.submissions s where s.slug = p.slug)
    or exists(select 1 from u.drafts d where d.slug = p.slug) then 'attempted'
  else 'todo' end"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _load_problem(con, slug: str) -> sqlite3.Row:
    row = con.execute(f"select p.*, {_STATUS_SQL} as status from problems p where p.slug = ?", (slug,)).fetchone()
    if not row:
        raise ServiceError(404, f"Unknown problem {slug!r}")
    return row


# ---------- queries ----------

def list_problems(q: str = "", difficulty: str = "", status: str = "", tags: str = "", company: str = "",
                  window: str = "6m", sort: str = "", page: int = 1, page_size: int = 50) -> dict:
    where, args = [], []
    join = ""
    freq = "null"
    if company:
        if window not in WINDOWS:
            raise ServiceError(400, f"window must be one of {WINDOWS}")
        join = "join company_problems cp on cp.slug = p.slug and cp.company = ? and cp.window = ?"
        args += [company, window]
        freq = "cp.frequency"
    if q:
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
        where.append("(" + " or ".join("exists(select 1 from json_each(p.tags) where value = ?)" for _ in tag_list) + ")")
        args += tag_list
    inner = f"select p.slug, p.frontend_id, p.title, p.difficulty, p.acceptance, p.tags, p.has_tests, " \
            f"{freq} as frequency, {_STATUS_SQL} as status from problems p {join}"
    if where:
        inner += " where " + " and ".join(where)
    outer = f"select * from ({inner})"
    if status:
        outer += " where status = ?"
        args.append(status)
    order = {"frequency": "frequency desc", "acceptance": "acceptance desc",
             "difficulty": "case difficulty when 'Easy' then 0 when 'Medium' then 1 else 2 end, frontend_id",
             "id": "frontend_id"}.get(sort or ("frequency" if company else "id"), "frontend_id")
    with _conn() as con:
        total = con.execute(f"select count(*) from ({outer})", args).fetchone()[0]
        rows = con.execute(f"{outer} order by {order}, frontend_id limit ? offset ?",
                           args + [page_size, (max(page, 1) - 1) * page_size]).fetchall()
        counts = {d.lower(): [0, 0] for d in ("Easy", "Medium", "Hard")}
        for r in con.execute(f"select difficulty, {_STATUS_SQL} = 'solved' as solved, count(*) from problems p "
                             f"group by 1, 2"):
            if r[0] and r[0].lower() in counts:
                counts[r[0].lower()][1] += r[2]
                if r[1]:
                    counts[r[0].lower()][0] += r[2]
    items = [{"slug": r["slug"], "id": r["frontend_id"], "title": r["title"], "difficulty": r["difficulty"],
              "acceptance": r["acceptance"], "tags": json.loads(r["tags"]), "frequency": r["frequency"],
              "status": r["status"], "has_tests": bool(r["has_tests"])} for r in rows]
    return {"total": total, "items": items, "counts": counts}


def all_tags() -> list[dict]:
    with _conn() as con:
        rows = con.execute("select value, count(*) from problems, json_each(problems.tags) group by 1 order by 2 desc")
        return [{"name": r[0], "count": r[1]} for r in rows]


def problem_detail(slug: str) -> dict:
    with _conn() as con:
        p = _load_problem(con, slug)
        starters = {r["lang"]: r["code"] for r in con.execute("select lang, code from starters where slug = ?", (slug,))}
        companies = [dict(r) for r in con.execute(
            "select c.slug, c.name, cp.frequency from company_problems cp join companies c on c.slug = cp.company "
            "where cp.slug = ? and cp.window = 'all' order by cp.frequency desc limit 30", (slug,))]
        prev = con.execute("select slug from problems where frontend_id < ? order by frontend_id desc limit 1",
                           (p["frontend_id"],)).fetchone()
        nxt = con.execute("select slug from problems where frontend_id > ? order by frontend_id limit 1",
                          (p["frontend_id"],)).fetchone()
    return {
        "slug": p["slug"], "id": p["frontend_id"], "title": p["title"], "difficulty": p["difficulty"],
        "tags": json.loads(p["tags"]), "acceptance": p["acceptance"], "description_html": p["description_html"],
        "params": json.loads(p["params"]) if p["params"] else [], "examples": json.loads(p["examples"] or "[]"),
        "has_tests": bool(p["has_tests"]), "langs": json.loads(p["langs"]), "starters": starters,
        "companies": companies, "status": p["status"],
        "prev": prev[0] if prev else None, "next": nxt[0] if nxt else None,
    }


def solutions(slug: str) -> list[dict]:
    with _conn() as con:
        _load_problem(con, slug)
        rows = con.execute("select title, explanation_md, code from solutions where slug = ? order by idx", (slug,))
        out = []
        for r in rows:
            code, notes = json.loads(r["code"]), {}
            if "kotlin" not in code and "java" in code:
                code["kotlin"] = code["java"]
                notes["kotlin"] = KOTLIN_FALLBACK_NOTE
            out.append({"title": r["title"], "explanation_md": r["explanation_md"], "code": code, "notes": notes})
        return out


# ---------- drafts & submissions ----------

def get_draft(slug: str, lang: str) -> str | None:
    with db.connect_user() as u:
        row = u.execute("select code from drafts where slug = ? and lang = ?", (slug, lang)).fetchone()
    return row[0] if row else None


def save_draft(slug: str, lang: str, code: str) -> None:
    if lang not in LANGS:
        raise ServiceError(400, f"Unknown language {lang!r}")
    with db.connect_user() as u:
        u.execute("insert into drafts values (?,?,?,?) on conflict(slug, lang) do update set code = excluded.code, "
                  "updated_at = excluded.updated_at", (slug, lang, code, _now()))


def list_submissions(slug: str) -> list[dict]:
    with db.connect_user() as u:
        rows = u.execute("select * from submissions where slug = ? order by id desc", (slug,)).fetchall()
    return [{**dict(r), "failing": json.loads(r["failing"]) if r["failing"] else None} for r in rows]


# ---------- judging ----------

def _request(p: sqlite3.Row, lang: str, code: str, cases: list[list], timeout_ms: int) -> dict:
    req = {"lang": lang, "code": code, "method": p["method"], "params": json.loads(p["params"]), "ret": p["ret"],
           "cases": cases, "timeout_ms": timeout_ms, "cpp_sig": None}
    if lang == "cpp":
        with _conn() as con:
            row = con.execute("select cpp_sig from starters where slug = ? and lang = 'cpp'", (p["slug"],)).fetchone()
        req["cpp_sig"] = json.loads(row[0])
    return req


def _check_runnable(p: sqlite3.Row, lang: str) -> None:
    if not p["has_tests"]:
        raise ServiceError(400, "No tests available for this problem")
    if lang not in json.loads(p["langs"]):
        raise ServiceError(400, f"{lang} is not available for this problem")


def _case_failure(res: dict, i: int) -> tuple[str, str | None]:
    """Verdict and error text for case i, given the runner result (case i was not a clean success)."""
    if i < len(res["results"]):
        err = res["results"][i].get("error") or ""
        return ("Memory Limit Exceeded" if any(m in err for m in _MEMORY_MARKERS) else "Runtime Error"), err
    if res["timed_out"]:
        return "Time Limit Exceeded", None
    code = res.get("exit_code", 0)
    if code == -9:
        return "Memory Limit Exceeded", "Process was killed (out of memory)"
    detail = _SIGNALS.get(code, f"Process exited with code {code}")
    stderr = (res.get("stderr") or "").strip()
    return "Runtime Error", detail + (f"\n{stderr[-2000:]}" if stderr else "")


def _expected_for(runner: Runner, p: sqlite3.Row, arg_lists: list[list]) -> list:
    missing = [a for a in arg_lists if (p["slug"], json.dumps(a)) not in _expected_cache]
    if missing:
        res = runner(_request(p, "python", p["ref_python"], missing, config.LIMITS["run_per_case_ms"] * len(missing)))
        for a, r in zip(missing, res["results"]):
            if r.get("ok"):
                _expected_cache[(p["slug"], json.dumps(a))] = r["value"]
    return [_expected_cache.get((p["slug"], json.dumps(a))) for a in arg_lists]


def _parse_custom(p: sqlite3.Row, custom: list[str]) -> list[list]:
    names = [x["name"] for x in json.loads(p["params"])]
    out = []
    for i, text in enumerate(custom, 1):
        try:
            kw = parse_kwargs(text)
        except ValueError as e:
            raise ServiceError(400, f"Custom case {i}: {e}") from e
        if set(kw) != set(names):
            raise ServiceError(400, f"Custom case {i} must set exactly: {', '.join(names)}")
        out.append([kw[n] for n in names])
    return out


def run(runner: Runner, slug: str, lang: str, code: str, custom: list[str] | None = None) -> dict:
    with _conn() as con:
        p = _load_problem(con, slug)
    _check_runnable(p, lang)
    arg_lists = json.loads(p["examples"]) + _parse_custom(p, custom or [])
    expected = _expected_for(runner, p, arg_lists)
    res = runner(_request(p, lang, code, arg_lists, config.LIMITS["run_per_case_ms"] * len(arg_lists)))
    if res["compile_error"]:
        return {"verdict": "Compile Error", "compile_error": res["compile_error"], "cases": []}
    cases, verdict = [], "Accepted"
    for i, (args, exp) in enumerate(zip(arg_lists, expected)):
        r = res["results"][i] if i < len(res["results"]) else None
        if r and r["ok"]:
            passed = exp is not None and judge(exp, r["value"], p["compare_mode"])
            cases.append({"args": args, "expected": exp, "actual": r["value"], "stdout": r["stdout"], "ok": passed,
                          "error": None if exp is not None else "Reference solution could not run this input",
                          "ms": r["ms"]})
            if not passed and verdict == "Accepted":
                verdict = "Wrong Answer"
        else:
            kind, err = _case_failure(res, i)
            cases.append({"args": args, "expected": exp, "actual": None, "stdout": r["stdout"] if r else "",
                          "ok": False, "error": err, "ms": None})
            if verdict == "Accepted":
                verdict = kind
    return {"verdict": verdict, "compile_error": None, "cases": cases}


def submit(runner: Runner, slug: str, lang: str, code: str) -> dict:
    with _conn() as con:
        p = _load_problem(con, slug)
        _check_runnable(p, lang)
        cases = json.loads(con.execute("select cases from tests where slug = ?", (slug,)).fetchone()[0])
    res = runner(_request(p, lang, code, [c["args"] for c in cases], config.LIMITS["submit_total_ms"]))
    out = {"verdict": "Accepted", "passed": 0, "total": len(cases), "runtime_ms": None, "memory_kb": res["memory_kb"],
           "failing": None, "compile_error": res["compile_error"]}
    if res["compile_error"]:
        out["verdict"] = "Compile Error"
    else:
        for i, c in enumerate(cases):
            r = res["results"][i] if i < len(res["results"]) else None
            if r and r["ok"] and judge(c["expected"], r["value"], p["compare_mode"]):
                out["passed"] += 1
                continue
            if r and r["ok"]:
                out["verdict"], err = "Wrong Answer", None
            else:
                out["verdict"], err = _case_failure(res, i)
            out["failing"] = {"args": c["args"], "expected": c["expected"], "actual": r["value"] if r and r["ok"] else None,
                              "stdout": r["stdout"] if r else "", "error": err}
            break
        if out["verdict"] == "Accepted":
            out["runtime_ms"] = round(sum(r["ms"] for r in res["results"]), 3)
    with db.connect_user() as u:
        cur = u.execute("insert into submissions (slug, lang, code, verdict, passed, total, runtime_ms, memory_kb, "
                        "failing, created_at) values (?,?,?,?,?,?,?,?,?,?)",
                        (slug, lang, code, out["verdict"], out["passed"], out["total"], out["runtime_ms"],
                         out["memory_kb"], json.dumps(out["failing"]) if out["failing"] else None, _now()))
        out["submission_id"] = cur.lastrowid
    return out


# ---------- companies & stats ----------

def list_companies(q: str = "") -> list[dict]:
    with _conn() as con:
        rows = con.execute("select c.slug, c.name, count(cp.slug) from companies c left join company_problems cp "
                           "on cp.company = c.slug and cp.window = 'all' where c.name like ? group by c.slug "
                           "order by 3 desc, c.name", (f"%{q}%",))
        return [{"slug": r[0], "name": r[1], "count": r[2]} for r in rows]


def company_summary(slug: str, window: str = "6m") -> dict:
    if window not in WINDOWS:
        raise ServiceError(400, f"window must be one of {WINDOWS}")
    with _conn() as con:
        c = con.execute("select * from companies where slug = ?", (slug,)).fetchone()
        if not c:
            raise ServiceError(404, f"Unknown company {slug!r}")
        windows = {w: 0 for w in WINDOWS}
        for r in con.execute("select window, count(*) from company_problems where company = ? group by 1", (slug,)):
            windows[r[0]] = r[1]
        rows = con.execute(f"select p.slug, p.frontend_id, p.title, p.difficulty, p.tags, cp.frequency, "
                           f"{_STATUS_SQL} as status from company_problems cp join problems p on p.slug = cp.slug "
                           f"where cp.company = ? and cp.window = ? order by cp.frequency desc", (slug, window)).fetchall()
        updated = con.execute("select value from meta where key = 'imported_at'").fetchone()
    by_diff = {"Easy": 0, "Medium": 0, "Hard": 0}
    topics: Counter = Counter()
    for r in rows:
        by_diff[r["difficulty"]] = by_diff.get(r["difficulty"], 0) + 1
        topics.update(json.loads(r["tags"]))
    unsolved = [r for r in rows if r["status"] != "solved"]
    return {
        "slug": slug, "name": c["name"], "window": window, "total": len(rows), "windows": windows,
        "by_difficulty": by_diff, "top_topics": [{"name": n, "count": k} for n, k in topics.most_common(8)],
        "solved": sum(r["status"] == "solved" for r in rows), "attempted": sum(r["status"] == "attempted" for r in rows),
        "next_unsolved": [{"slug": r["slug"], "id": r["frontend_id"], "title": r["title"], "difficulty": r["difficulty"]}
                          for r in unsolved[:3]],
        "updated": updated[0] if updated else None,
    }


def stats() -> dict:
    with _conn() as con:
        firsts = con.execute("select s.slug, min(s.created_at) as at, p.difficulty, p.tags from u.submissions s "
                             "join problems p on p.slug = s.slug where s.verdict = 'Accepted' group by s.slug").fetchall()
        totals = {d.lower(): [0, 0] for d in ("Easy", "Medium", "Hard")}
        for r in con.execute("select difficulty, count(*) from problems group by 1"):
            if r[0] and r[0].lower() in totals:
                totals[r[0].lower()][1] = r[1]
        topic_totals = Counter({r[0]: r[1] for r in con.execute(
            "select value, count(*) from problems, json_each(problems.tags) group by 1")})
        solved_slugs = [r["slug"] for r in firsts]
        by_company = []
        if solved_slugs:
            marks = ",".join("?" * len(solved_slugs))
            by_company = [{"slug": r[0], "name": r[1], "solved": r[2], "total": r[3]} for r in con.execute(
                f"select c.slug, c.name, sum(cp.slug in ({marks})), count(*) from company_problems cp "
                f"join companies c on c.slug = cp.company where cp.window = '6m' group by c.slug "
                f"order by 3 desc, 4 desc limit 8", solved_slugs)]
        first_sub = con.execute("select min(created_at) from u.submissions").fetchone()[0]
    weeks: dict[str, dict] = defaultdict(lambda: {"easy": 0, "medium": 0, "hard": 0})
    topic_solved: Counter = Counter()
    for r in firsts:
        d = datetime.fromisoformat(r["at"]).date()
        week = (d - timedelta(days=d.weekday())).isoformat()
        weeks[week][r["difficulty"].lower()] += 1
        totals[r["difficulty"].lower()][0] += 1
        topic_solved.update(json.loads(r["tags"]))
    start = date.today() - timedelta(weeks=25)
    start -= timedelta(days=start.weekday())
    series = []
    for i in range(26):
        wk = (start + timedelta(weeks=i)).isoformat()
        series.append({"week": wk, **weeks.get(wk, {"easy": 0, "medium": 0, "hard": 0})})
    return {
        "since": first_sub, "totals": totals, "solved_by_week": series,
        "by_topic": [{"name": n, "solved": topic_solved[n], "total": t} for n, t in topic_totals.most_common(12)],
        "by_company": by_company,
    }


def export() -> dict:
    with db.connect_user() as u:
        return {"exported_at": _now(),
                "drafts": [dict(r) for r in u.execute("select * from drafts")],
                "submissions": [dict(r) for r in u.execute("select * from submissions")]}
