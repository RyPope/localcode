"""Merge upstream sources and repo-kept content into a fresh content.db (built in a temp file, then swapped in)."""

import html
import json
import re
import sqlite3
from collections.abc import Callable
from contextlib import suppress
from datetime import UTC, datetime
from pathlib import Path

from localcode import config, db
from localcode.importer.case_filter import case_key, filter_cases
from localcode.importer.companies import load_companies
from localcode.importer.dataset import DatasetProblem, load_rows, params_from_starter
from localcode.importer.doocs import DoocsProblem, iter_problem_dirs, parse_problem_dir
from localcode.importer.local import LocalProblem, load_local
from localcode.importer.signatures import cpp_starter, java_starter, kotlin_starter, parse_cpp_sig, parse_java_sig
from localcode.judging.answer_modes import answer_mode

Progress = Callable[[str, int, int], None]
EXCLUDED_CASES = Path(__file__).resolve().parent.parent / "data" / "excluded_cases.json"
MIN_CASES = 3


def load_excluded(path: Path = EXCLUDED_CASES) -> dict[str, set[str]]:
    """Known-bad case keys per problem, produced by `python -m localcode.tools.validate_cases`."""
    if not path.exists():
        return {}
    return {slug: set(keys) for slug, keys in json.loads(path.read_text()).items()}


def _title_from_slug(slug: str) -> str:
    return " ".join(w.capitalize() for w in slug.split("-"))


def _sig(parse, code: str | None, method: str | None, nparams: int | None) -> dict | None:
    if not code:
        return None
    try:
        sig = parse(code)
    except ValueError:
        return None
    if method is not None and (sig["method"] != method or len(sig["params"]) != nparams):
        return None
    return sig


def _python_starter(code: str, method: str) -> str:
    """`class Solution:` and the method header from a Python solution, with an empty body."""
    for line in code.splitlines():
        if re.match(rf"\s*def {re.escape(method)}\(", line):
            return f"class Solution:\n    {line.strip()}\n        \n"
    raise ValueError(f"no def {method} in Python solution")


def _local_signature(local: LocalProblem | None) -> tuple[str, str, list[dict], str] | None:
    """(code, method, params, ret) from a local Python solution, if it has a usable one."""
    for s in local.solutions if local else []:
        if "python" in s.code:
            with suppress(ValueError):
                return (s.code["python"], *params_from_starter(s.code["python"]))
    return None


def _merge_cases(upstream: list[dict], local: list[dict]) -> list[dict]:
    """Upstream cases with local ones replacing those with the same args, then the new local ones."""
    by_key = {case_key(c["args"]): c for c in upstream}
    for c in local:
        by_key[case_key(c["args"])] = c
    return list(by_key.values())


def _problem_rows(
    ds: DatasetProblem | None,
    dc: DoocsProblem | None,
    local: LocalProblem | None,
    acceptance: float | None,
    excluded: set[str],
    local_owned: bool = False,
):
    slug = (ds or dc or local).slug
    upstream = ds is not None or dc is not None
    local_sig = _local_signature(local)
    # A local Python solution defines the problem when nothing upstream can, or when it always has.
    use_local = local_sig is not None and (not upstream or local_owned or not (ds and ds.has_tests))
    if use_local:
        ref_python, method, params, ret = local_sig
        compare_mode = "exact"
    elif ds:
        ref_python, method, params, ret, compare_mode = ds.ref_python, ds.method, ds.params, ds.ret, ds.compare_mode
    else:
        ref_python = method = params = ret = None
        compare_mode = "exact"
    compare_mode = answer_mode(slug, compare_mode)
    if local and local.compare_mode:
        compare_mode = local.compare_mode
    nparams = len(params) if params is not None else None

    upstream_solutions = dc.solutions if dc else []
    local_solutions = local.solutions if local else []
    codes = [s["code"] for s in upstream_solutions] + [s.code for s in local_solutions]

    def sig_for(lang: str, parse) -> dict | None:
        for code in codes:
            if sig := _sig(parse, code.get(lang), method, nparams):
                return sig
        return None

    java = sig_for("java", parse_java_sig)
    cpp = sig_for("cpp", parse_cpp_sig)

    starters = []
    if use_local:
        starters.append((slug, "python", _python_starter(ref_python, method), None))
    elif ds:
        starters.append((slug, "python", ds.starter_python, None))
    if java:
        starters.append((slug, "java", java_starter(java), None))
        with suppress(ValueError):  # a Java type with no Kotlin mapping: no Kotlin for this problem
            starters.append((slug, "kotlin", kotlin_starter(java), None))
    if cpp:
        starters.append((slug, "cpp", cpp_starter(cpp), json.dumps(cpp)))

    cases = filter_cases(ds.cases, ret, java, excluded) if ds and not use_local else []
    if local and local.cases and ret is not None:
        cases = _merge_cases(cases, filter_cases(local.cases, ret, java, set()))
    if nparams is not None:
        cases = [c for c in cases if len(c["args"]) == nparams]
    has_tests = method is not None and ret != "None" and len(cases) >= MIN_CASES
    langs = [lang for lang in ("python", "java", "cpp", "kotlin") if has_tests and any(s[1] == lang for s in starters)]
    examples = ds.examples if ds and ds.examples and not use_local else [c["args"] for c in cases[:MIN_CASES]]

    if local and local.description_html:
        description = local.description_html
    elif dc and dc.description_html:
        description = dc.description_html
    elif ds:
        description = f'<pre class="plain">{html.escape(ds.description)}</pre>'
    else:
        description = ""
    tags = (local and local.tags) or (dc.tags if dc and dc.tags else (ds.tags if ds else []))
    difficulty = (local and local.difficulty) or (
        dc.difficulty if dc and dc.difficulty else (ds.difficulty if ds else "")
    )
    frontend_id = (local and local.frontend_id) or (dc.frontend_id if dc else (ds.frontend_id if ds else None))
    title = (local and local.title) or (dc.title if dc else _title_from_slug(slug))
    source = "local" if use_local or not upstream else "upstream"
    problem = (
        slug,
        frontend_id,
        title,
        difficulty,
        json.dumps(tags),
        acceptance,
        description,
        method,
        json.dumps(params) if params is not None else None,
        ret,
        compare_mode,
        json.dumps(examples),
        ref_python,
        int(has_tests),
        json.dumps(langs),
        source,
    )
    solutions = [
        (slug, i, s["title"], s["explanation_md"], json.dumps(s["code"]), "upstream")
        for i, s in enumerate(upstream_solutions)
    ] + [
        (slug, len(upstream_solutions) + i, s.title, s.explanation_md, json.dumps(s.code), "local")
        for i, s in enumerate(local_solutions)
    ]
    tests = (slug, json.dumps(cases)) if has_tests else None
    return problem, starters, solutions, tests


PROBLEM_FILL = ("frontend_id", "title", "difficulty", "tags", "description_html", "acceptance")
SIGNATURE = ("method", "params", "ret", "ref_python", "compare_mode", "examples")
_EMPTY = (None, "", "[]")


def _columns(con: sqlite3.Connection, table: str, schema: str = "main") -> list[str]:
    return [r[1] for r in con.execute(f"pragma {schema}.table_info({table})")]


def _locally_owned(previous: Path | None) -> set[str]:
    """Slugs the previous import took from local content (they keep their local signature)."""
    if not previous:
        return set()
    con = sqlite3.connect(f"{previous.as_uri()}?mode=ro", uri=True)
    try:
        if "source" not in _columns(con, "problems"):
            return set()
        return {r[0] for r in con.execute("select slug from problems where source = 'local'")}
    finally:
        con.close()


def _copy_rows(con: sqlite3.Connection, table: str, where: str, args: tuple, overrides: dict | None = None) -> int:
    """Copy rows of `table` from the attached previous database, defaulting `source` to upstream."""
    cols = _columns(con, table)
    old = set(_columns(con, table, "prev"))
    exprs = [
        "?" if overrides and c in overrides else (c if c in old else ("'upstream'" if c == "source" else "null"))
        for c in cols
    ]
    params = tuple(overrides[c] for c in cols if overrides and c in overrides)
    cur = con.execute(
        f"insert into main.{table} ({', '.join(cols)}) select {', '.join(exprs)} from prev.{table} where {where}",
        params + args,
    )
    return cur.rowcount


def _carry_forward(
    con: sqlite3.Connection, previous: Path, excluded: dict[str, set[str]], local_slugs: set[str]
) -> dict:
    """Keep everything the previous content.db had that this build lacks; never override new values."""
    kept = {"kept_problems": 0, "kept_solutions": 0, "kept_cases": 0}
    con.execute("attach database ? as prev", (str(previous),))
    try:
        new_slugs = {r[0] for r in con.execute("select slug from main.problems")}
        for (slug,) in con.execute("select slug from prev.problems").fetchall():
            if slug not in new_slugs:
                _copy_rows(con, "problems", "slug = ?", (slug,))
                for table in ("starters", "solutions", "tests"):
                    _copy_rows(con, table, "slug = ?", (slug,))
                kept["kept_problems"] += 1
                continue
            _merge_previous(con, slug, excluded.get(slug, set()), kept, slug in local_slugs)
    finally:
        con.commit()
        con.execute("detach database prev")
    return kept


def _merge_previous(con: sqlite3.Connection, slug: str, excluded: set[str], kept: dict, has_folder: bool) -> None:
    """Fold the previous import's rows for `slug` into the new ones.

    While a problem's content/ folder exists it is the record of its local solutions (so renaming one
    doesn't leave a copy behind); once the folder is gone, its local solutions are kept like any other.
    """
    new = con.execute("select * from main.problems where slug = ?", (slug,)).fetchone()
    old = con.execute("select * from prev.problems where slug = ?", (slug,)).fetchone()
    old_cols = set(old.keys())
    fill = {c: old[c] for c in PROBLEM_FILL if c in old_cols and new[c] in _EMPTY and old[c] not in _EMPTY}
    if new["method"] is None and old["method"] is not None:  # the source lost its signature: keep the old one
        fill.update({c: old[c] for c in SIGNATURE})
    if fill:
        con.execute(
            f"update main.problems set {', '.join(f'{c} = ?' for c in fill)} where slug = ?", (*fill.values(), slug)
        )
        new = con.execute("select * from main.problems where slug = ?", (slug,)).fetchone()
    same_signature = (new["method"], new["params"]) == (old["method"], old["params"])
    if same_signature:
        _copy_rows(
            con, "starters", "slug = ? and lang not in (select lang from main.starters where slug = ?)", (slug, slug)
        )

    have = {tuple(r) for r in con.execute("select title, source from main.solutions where slug = ?", (slug,))}
    old_source = "source" if "source" in _columns(con, "solutions", "prev") else "'upstream'"
    next_idx = con.execute("select coalesce(max(idx), -1) + 1 from main.solutions where slug = ?", (slug,)).fetchone()[
        0
    ]
    for idx, title, source in con.execute(
        f"select idx, title, {old_source} from prev.solutions where slug = ? order by idx", (slug,)
    ).fetchall():
        if (title, source) not in have and not (has_folder and source == "local"):
            _copy_rows(con, "solutions", "slug = ? and idx = ?", (slug, idx), {"idx": next_idx})
            next_idx += 1
            kept["kept_solutions"] += 1

    if new["method"] is None or (new["params"], new["ret"]) != (old["params"], old["ret"]):
        return  # cases written for another signature can't be judged against this one
    row = con.execute("select cases from main.tests where slug = ?", (slug,)).fetchone()
    cases = json.loads(row[0]) if row else []
    old_row = con.execute("select cases from prev.tests where slug = ?", (slug,)).fetchone()
    params = json.loads(new["params"])
    java_row = con.execute("select code from main.starters where slug = ? and lang = 'java'", (slug,)).fetchone()
    java = _sig(parse_java_sig, java_row[0] if java_row else None, new["method"], len(params))
    keys = {case_key(c["args"]) for c in cases}
    extra = [
        c
        for c in (json.loads(old_row[0]) if old_row else [])
        if case_key(c["args"]) not in keys and len(c["args"]) == len(params)
    ]
    extra = filter_cases(extra, new["ret"], java, excluded)
    if not extra:
        return
    cases += extra
    kept["kept_cases"] += len(extra)
    con.execute("insert or replace into main.tests values (?, ?)", (slug, json.dumps(cases)))
    has_tests = new["ret"] != "None" and len(cases) >= MIN_CASES
    have_langs = {r[0] for r in con.execute("select lang from main.starters where slug = ?", (slug,))}
    langs = [lang for lang in ("python", "java", "cpp", "kotlin") if has_tests and lang in have_langs]
    examples = json.loads(new["examples"] or "[]") or [c["args"] for c in cases[:MIN_CASES]]
    con.execute(
        "update main.problems set has_tests = ?, langs = ?, examples = ? where slug = ?",
        (int(has_tests), json.dumps(langs), json.dumps(examples), slug),
    )


def _write_content(
    con: sqlite3.Connection,
    dataset: dict[str, DatasetProblem],
    doocs: dict[str, DoocsProblem],
    local: dict[str, LocalProblem],
    company_rows: list[tuple],
    excluded: dict[str, set[str]],
    sources_used: dict,
    progress: Progress,
    skipped: list[dict],
    local_owned: set[str] = frozenset(),
    previous: Path | None = None,
) -> dict:
    """Insert every problem, its starters, solutions, tests and company rows; returns import stats."""
    acceptance = {r[3]: r[5] for r in company_rows if r[5] is not None}
    slugs = sorted(set(dataset) | set(doocs) | set(local))
    for i, slug in enumerate(slugs):
        problem, starters, solutions, tests = _problem_rows(
            dataset.get(slug),
            doocs.get(slug),
            local.get(slug),
            acceptance.get(slug),
            excluded.get(slug, set()),
            slug in local_owned,
        )
        con.execute("insert into problems values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", problem)
        con.executemany("insert into starters values (?,?,?,?)", starters)
        con.executemany("insert into solutions values (?,?,?,?,?,?)", solutions)
        if tests:
            con.execute("insert into tests values (?,?)", tests)
        if i % 250 == 0:
            progress("tests", i, len(slugs))
    progress("tests", len(slugs), len(slugs))

    known = set(slugs)
    names = {}
    for company, name, window, slug, freq, _ in company_rows:
        if slug in known:
            names[company] = name
            con.execute("insert or replace into company_problems values (?,?,?,?)", (company, slug, window, freq))
    con.executemany("insert into companies values (?,?)", sorted(names.items()))
    progress("companies", len(names), len(names))

    kept = (
        _carry_forward(con, previous, excluded, set(local))
        if previous
        else {"kept_problems": 0, "kept_solutions": 0, "kept_cases": 0}
    )
    stats = {
        "problems": con.execute("select count(*) from problems").fetchone()[0],
        "with_tests": con.execute("select count(*) from problems where has_tests=1").fetchone()[0],
        "cases": con.execute("select coalesce(sum(json_array_length(cases)), 0) from tests").fetchone()[0],
        "companies": len(names),
        "local_problems": con.execute("select count(*) from problems where source = 'local'").fetchone()[0],
        "local_solutions": con.execute("select count(*) from solutions where source = 'local'").fetchone()[0],
        "skipped": skipped,
        **kept,
    }
    meta = {
        "imported_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "stats": json.dumps(stats),
        "sources": json.dumps(sources_used),
    }
    con.executemany("insert into meta values (?,?)", meta.items())
    return stats


def build_content_db(
    src: Path,
    out: Path,
    progress: Progress,
    sources_used: dict | None = None,
    excluded: dict[str, set[str]] | None = None,
    content_dir: Path | None = None,
    previous: Path | None = None,
) -> dict:
    """Build `out` from the downloaded sources in `src` and the repo content in `content_dir`.

    Anything in `previous` (default: the existing `out`) that this build lacks is carried forward.
    """
    previous = previous or (out if out.exists() else None)
    excluded = load_excluded() if excluded is None else excluded
    progress("problems", 0, 0)
    dataset: dict[str, DatasetProblem] = {}
    for f in config.DATASET_FILES:
        if (src / "dataset" / f).exists():
            for p in load_rows(src / "dataset" / f):
                dataset[p.slug] = p
    progress("problems", len(dataset), len(dataset))

    dirs = list(iter_problem_dirs(src / "doocs"))
    doocs: dict[str, DoocsProblem] = {}
    for i, d in enumerate(dirs):
        p = parse_problem_dir(d)
        if p:
            doocs[p.slug] = p
        if i % 250 == 0:
            progress("solutions", i, len(dirs))
    progress("solutions", len(dirs), len(dirs))

    company_rows = list(load_companies(src / "companies")) if (src / "companies").exists() else []
    local, skipped = load_local(content_dir) if content_dir else ({}, [])

    tmp = out.with_suffix(".tmp")
    tmp.unlink(missing_ok=True)
    con = db.connect_content(tmp)
    try:
        stats = _write_content(
            con,
            dataset,
            doocs,
            local,
            company_rows,
            excluded,
            sources_used or {},
            progress,
            skipped,
            _locally_owned(previous),
            previous,
        )
        con.commit()
    except BaseException:
        con.close()
        tmp.unlink(missing_ok=True)  # the previous content.db stays in place
        raise
    con.close()
    tmp.replace(out)
    progress("done", 1, 1)
    return stats
