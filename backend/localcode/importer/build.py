"""Merge the three sources into a fresh content.db (written to a temp file, then swapped in)."""

import html
import json
from collections.abc import Callable
from contextlib import suppress
from datetime import UTC, datetime
from pathlib import Path

from localcode import config, db
from localcode.importer.case_filter import filter_cases
from localcode.importer.companies import load_companies
from localcode.importer.dataset import DatasetProblem, load_rows
from localcode.importer.doocs import DoocsProblem, iter_problem_dirs, parse_problem_dir
from localcode.importer.signatures import cpp_starter, java_starter, kotlin_starter, parse_cpp_sig, parse_java_sig

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


def _problem_rows(ds: DatasetProblem | None, dc: DoocsProblem | None, acceptance: float | None, excluded: set[str]):
    slug = (ds or dc).slug
    method = ds.method if ds else None
    nparams = len(ds.params) if ds else None
    java = _sig(parse_java_sig, dc and dc.first_code("java"), method, nparams)
    cpp = _sig(parse_cpp_sig, dc and dc.first_code("cpp"), method, nparams)

    starters = []
    if ds:
        starters.append((slug, "python", ds.starter_python, None))
    if java:
        starters.append((slug, "java", java_starter(java), None))
        with suppress(ValueError):  # a Java type with no Kotlin mapping: no Kotlin for this problem
            starters.append((slug, "kotlin", kotlin_starter(java), None))
    if cpp:
        starters.append((slug, "cpp", cpp_starter(cpp), json.dumps(cpp)))

    cases = filter_cases(ds.cases, ds.ret, java, excluded) if ds else []
    has_tests = bool(ds and ds.has_tests and len(cases) >= MIN_CASES)
    langs = [lang for lang in ("python", "java", "cpp", "kotlin") if has_tests and any(s[1] == lang for s in starters)]
    examples = (ds.examples or [c["args"] for c in cases[:MIN_CASES]]) if ds else []
    description = (
        dc.description_html
        if dc and dc.description_html
        else (f'<pre class="plain">{html.escape(ds.description)}</pre>' if ds else "")
    )
    problem = (
        slug,
        dc.frontend_id if dc else ds.frontend_id,
        dc.title if dc else _title_from_slug(slug),
        (dc.difficulty if dc and dc.difficulty else ds.difficulty) if (dc or ds) else "",
        json.dumps(dc.tags if dc and dc.tags else (ds.tags if ds else [])),
        acceptance,
        description,
        method,
        json.dumps(ds.params) if ds else None,
        ds.ret if ds else None,
        ds.compare_mode if ds else "exact",
        json.dumps(examples),
        ds.ref_python if ds else None,
        int(has_tests),
        json.dumps(langs),
    )
    solutions = [
        (slug, i, s["title"], s["explanation_md"], json.dumps(s["code"]))
        for i, s in enumerate(dc.solutions if dc else [])
    ]
    tests = (slug, json.dumps(cases)) if has_tests else None
    return problem, starters, solutions, tests


def build_content_db(
    src: Path,
    out: Path,
    progress: Progress,
    sources_used: dict | None = None,
    excluded: dict[str, set[str]] | None = None,
) -> dict:
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
    acceptance = {r[3]: r[5] for r in company_rows if r[5] is not None}

    tmp = out.with_suffix(".tmp")
    tmp.unlink(missing_ok=True)
    con = db.connect_content(tmp)
    slugs = sorted(set(dataset) | set(doocs))
    for i, slug in enumerate(slugs):
        problem, starters, solutions, tests = _problem_rows(
            dataset.get(slug), doocs.get(slug), acceptance.get(slug), excluded.get(slug, set())
        )
        con.execute("insert into problems values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", problem)
        con.executemany("insert into starters values (?,?,?,?)", starters)
        con.executemany("insert into solutions values (?,?,?,?,?)", solutions)
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

    stats = {
        "problems": len(slugs),
        "with_tests": con.execute("select count(*) from problems where has_tests=1").fetchone()[0],
        "cases": con.execute("select coalesce(sum(json_array_length(cases)), 0) from tests").fetchone()[0],
        "companies": len(names),
    }
    meta = {
        "imported_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "stats": json.dumps(stats),
        "sources": json.dumps(sources_used or {}),
    }
    con.executemany("insert into meta values (?,?)", meta.items())
    con.commit()
    con.close()
    tmp.replace(out)
    progress("done", 1, 1)
    return stats
