"""Maintainer tool: find generated test cases that typed reference solutions reject.

Runs the doocs Java and C++ reference solutions over every problem's suite and records cases that
every *trusted* typed reference fails (a reference is trusted when it passes most of the suite).
Those cases almost always violate the problem's constraints. The output is our own derived data,
shipped as localcode/data/excluded_cases.json and applied by the importer.

Run inside the app container (it needs the runner and an imported content.db):

    docker compose exec app python -m localcode.tools.validate_cases /data/excluded_cases.json
"""

import argparse
import json
import queue
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from localcode import config
from localcode.db import content_session
from localcode.importer.case_filter import case_key
from localcode.judging import runner_client
from localcode.judging.compare import judge

TRUST_THRESHOLD = 0.5
TIMEOUT_MS = 30_000
REFERENCE_LANGS = ("java", "cpp")


def cases_to_exclude(outcomes: dict[str, list[bool]]) -> set[int]:
    """Indices failed by every reference that passes at least TRUST_THRESHOLD of the suite."""
    trusted = [o for o in outcomes.values() if o and sum(o) / len(o) >= TRUST_THRESHOLD]
    if not trusted:
        return set()
    return {i for i in range(len(trusted[0])) if not any(o[i] for o in trusted)}


def _outcomes(
    problem, lang: str, code: str, cases: list[dict], cpp_sig: dict | None, runner_url: str | None
) -> list[bool]:
    """Per-case pass/fail. A case that hangs or crashes fails; the cases after it are run again."""
    ok = [False] * len(cases)
    pending = list(range(len(cases)))
    while pending:
        chunk, pending = pending, []
        res = runner_client.execute(
            {
                "lang": lang,
                "code": code,
                "method": problem["method"],
                "params": json.loads(problem["params"]),
                "ret": problem["ret"],
                "cases": [cases[i]["args"] for i in chunk],
                "timeout_ms": TIMEOUT_MS,
                "memory_mb": config.LIMITS.memory_mb,
                "cpp_sig": cpp_sig,
            },
            runner_url,
        )
        if res["compile_error"]:
            return [False] * len(cases)
        for i, r in zip(chunk, res["results"], strict=False):
            ok[i] = bool(r.get("ok")) and judge(cases[i]["expected"], r["value"], problem["compare_mode"])
        done = len(res["results"])
        if done < len(chunk):  # chunk[done] hung or crashed the process; retry what followed it
            pending = chunk[done + 1 :]
    return ok


def _load(slug: str) -> tuple[dict, list[dict], dict[str, str], dict | None]:
    with content_session() as con:
        p = dict(con.execute("select * from problems where slug = ?", (slug,)).fetchone())
        cases = json.loads(con.execute("select cases from tests where slug = ?", (slug,)).fetchone()[0])
        codes: dict[str, str] = {}
        for (code,) in con.execute("select code from solutions where slug = ? order by idx", (slug,)):
            for lang, src in json.loads(code).items():
                codes.setdefault(lang, src)
        cpp_row = con.execute("select cpp_sig from starters where slug = ? and lang = 'cpp'", (slug,)).fetchone()
    return p, cases, codes, json.loads(cpp_row[0]) if cpp_row else None


def _validate_one(slug: str, runner_url: str | None) -> tuple[list[str], dict[str, str]]:
    p, cases, codes, cpp_sig = _load(slug)
    outcomes = {
        lang: _outcomes(p, lang, codes[lang], cases, cpp_sig if lang == "cpp" else None, runner_url)
        for lang in REFERENCE_LANGS
        if lang in codes and lang in json.loads(p["langs"])
    }
    bad = cases_to_exclude(outcomes)
    return sorted(case_key(cases[i]["args"]) for i in bad), {k: f"{sum(o)}/{len(o)}" for k, o in outcomes.items()}


def validate(out: Path, only: list[str] | None = None, runners: list[str] | None = None) -> dict[str, list[str]]:
    """Validate every runnable problem, one worker per runner URL (default: the configured runner)."""
    with content_session() as con:
        slugs = [r[0] for r in con.execute("select slug from problems where has_tests = 1 order by frontend_id")]
    result: dict[str, list[str]] = json.loads(out.read_text()) if out.exists() else {}
    todo = [s for s in slugs if s in only] if only else [s for s in slugs if s not in result]
    lock = threading.Lock()
    done = 0
    pool_urls: queue.Queue[str | None] = queue.Queue()
    for url in runners or [None]:
        pool_urls.put(url)

    def work(slug: str) -> None:
        nonlocal done
        url = pool_urls.get()
        try:
            keys, summary = _validate_one(slug, url)
        finally:
            pool_urls.put(url)
        with lock:
            done += 1
            result[slug] = keys
            out.write_text(json.dumps(result, indent=0, sort_keys=True))
            print(f"[{done}/{len(todo)}] {slug}: {summary} exclude {len(keys)}", flush=True)

    with ThreadPoolExecutor(max_workers=len(runners or [None])) as pool:
        for f in [pool.submit(work, s) for s in todo]:
            f.result()
    return result


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("out", type=Path, help="JSON file to write (resumes if it exists)")
    ap.add_argument("--only", nargs="*", help="limit to these problem slugs")
    ap.add_argument(
        "--runners",
        nargs="*",
        help="runner base URLs to spread work across, e.g. http://localcode-runner-1:8080 (default: LOCALCODE_RUNNER)",
    )
    args = ap.parse_args(argv)
    t0 = time.time()
    result = validate(args.out, args.only, args.runners)
    print(
        f"done: {sum(map(len, result.values()))} cases excluded across {len(result)} problems "
        f"in {time.time() - t0:.0f}s",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
