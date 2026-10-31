"""Check the repo's content/ folder: every file parses and every local solution passes its tests.

Builds a throwaway content.db from content/ (on its own, or over the downloaded upstream sources with
--full) using the importer itself, then runs each local solution in each of its languages in the
runner sandbox. Run inside the app container, where the runner is reachable:

    docker compose exec -T app python -m localcode.tools.validate_content          # what CI runs
    docker compose exec -T app python -m localcode.tools.validate_content --full   # also upstream tests
"""

import argparse
import json
import sqlite3
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path

from localcode import config
from localcode.importer.build import MIN_CASES, build_content_db
from localcode.importer.dataset import params_from_starter
from localcode.importer.local import load_local
from localcode.importer.signatures import parse_cpp_sig, parse_java_sig
from localcode.judging import runner_client
from localcode.judging.compare import judge

TIMEOUT_MS = 30_000
PARSERS = {"java": parse_java_sig, "cpp": parse_cpp_sig, "python": params_from_starter}

Execute = Callable[..., dict]


def _short(value) -> str:
    text = json.dumps(value)
    return text if len(text) <= 120 else text[:117] + "..."


def _run(execute: Execute, p: sqlite3.Row, lang: str, code: str, cases: list[dict], cpp_sig: dict | None) -> str | None:
    """None if `code` passes every case, else what went wrong."""
    res = execute(
        {
            "lang": lang,
            "code": code,
            "method": p["method"],
            "params": json.loads(p["params"]),
            "ret": p["ret"],
            "cases": [c["args"] for c in cases],
            "timeout_ms": TIMEOUT_MS,
            "memory_mb": config.LIMITS.memory_mb,
            "cpp_sig": cpp_sig,
        }
    )
    if res.get("compile_error"):
        return f"does not compile: {res['compile_error'].strip()[:500]}"
    results = res.get("results", [])
    for i, case in enumerate(cases):
        if i >= len(results):
            return f"crashed or timed out on case {i + 1}: args {_short(case['args'])}"
        r = results[i]
        if not r.get("ok"):
            return f"raised on case {i + 1}: args {_short(case['args'])}: {str(r.get('error', ''))[:300]}"
        if not judge(case["expected"], r["value"], p["compare_mode"]):
            return (
                f"fails case {i + 1}: args {_short(case['args'])}, expected {_short(case['expected'])}, "
                f"got {_short(r['value'])}"
            )
    return None


def _why_not_runnable(p: sqlite3.Row, cases: int) -> str:
    if p is None or p["method"] is None:
        return "needs a solution with Python code to define the function signature"
    if p["ret"] == "None":
        return "the function must return a value (in-place problems can't be judged)"
    return f"needs at least {MIN_CASES} test cases that fit the signature (has {cases})"


def validate(root: Path, execute: Execute = runner_client.execute, sources: Path | None = None) -> list[str]:
    """Every problem in `root` (content/), built alone or over upstream `sources`; returns error messages."""
    local, skipped = load_local(root)
    errors = [f"{s['path']}: {s['reason']}" for s in skipped]
    with tempfile.TemporaryDirectory() as tmp:
        src = sources or Path(tmp) / "no-sources"
        out = Path(tmp) / "content.db"
        build_content_db(src, out, progress=lambda *a: None, excluded={}, content_dir=root)
        con = sqlite3.connect(out)
        con.row_factory = sqlite3.Row
        try:
            for slug, lp in local.items():
                where = root / "problems" / slug
                p = con.execute("select * from problems where slug = ?", (slug,)).fetchone()
                row = con.execute("select cases from tests where slug = ?", (slug,)).fetchone()
                cases = json.loads(row[0]) if row else []
                langs = set(json.loads(p["langs"])) if p else set()
                defines = lp.cases is not None  # a folder with its own tests must run on its own
                if not (p and p["has_tests"]):
                    if defines:
                        errors.append(f"{where}: can't be run: {_why_not_runnable(p, len(cases))}")
                    for s in lp.solutions:  # an overlay we can't run here: at least check its signatures parse
                        for lang, code in s.code.items():
                            if lang in PARSERS:
                                try:
                                    PARSERS[lang](code)
                                except ValueError as e:
                                    errors.append(f"{where}: solution {s.title!r} ({lang}): {e}")
                    continue
                cpp = con.execute("select cpp_sig from starters where slug = ? and lang = 'cpp'", (slug,)).fetchone()
                for s in lp.solutions:
                    for lang, code in s.code.items():
                        if lang not in langs:
                            errors.append(
                                f"{where}: solution {s.title!r} ({lang}): signature doesn't match the problem's"
                            )
                            continue
                        problem = _run(
                            execute, p, lang, code, cases, json.loads(cpp[0]) if cpp and lang == "cpp" else None
                        )
                        if problem:
                            errors.append(f"{where}: solution {s.title!r} ({lang}) {problem}")
        finally:
            con.close()
    return errors


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("root", nargs="?", type=Path, default=config.CONTENT_DIR, help="the content/ folder")
    ap.add_argument("--full", action="store_true", help="merge over the downloaded upstream sources first")
    args = ap.parse_args(argv)
    local, _ = load_local(args.root)
    errors = validate(args.root, sources=config.SOURCES_DIR if args.full else None)
    for e in errors:
        print(f"error: {e}", flush=True)
    print(f"{len(local)} problem folders checked, {len(errors)} errors", flush=True)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
