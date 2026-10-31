"""Maintainer tool: find generated test cases that typed reference solutions reject.

Runs the doocs Java and C++ reference solutions over every problem's suite and records cases that
every *trusted* typed reference fails, or that one *confident* reference fails (see the thresholds).
Those cases almost always violate the problem's constraints: a correct typed solution crashes or
disagrees on them, while another language may get lucky (C++ reads out of bounds without crashing).
The output is our own derived data, shipped as localcode/data/excluded_cases.json and applied by the
importer.

Run inside the app container (it needs the runner and an imported content.db):

    docker compose exec -u localcode app python -m localcode.tools.validate_cases /data/excluded_cases.json
"""

import argparse
import json
import queue
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from localcode import config
from localcode.db import content_session
from localcode.importer.case_filter import case_key
from localcode.judging import runner_client
from localcode.judging.compare import judge

# A reference is trusted when it passes at least TRUST_THRESHOLD of a suite; trusted references that
# agree on a failure exclude the case. A reference passing CONFIDENT_THRESHOLD excludes on its own.
TRUST_THRESHOLD = 0.5
CONFIDENT_THRESHOLD = 0.9
TIMEOUT_MS = 30_000
REFERENCE_LANGS = ("java", "cpp")


def cases_to_exclude(outcomes: dict[str, list[bool]]) -> set[int]:
    """Indices failed by every trusted reference, or by any confident one."""
    rates = {lang: sum(o) / len(o) for lang, o in outcomes.items() if o}
    trusted = [outcomes[lang] for lang, rate in rates.items() if rate >= TRUST_THRESHOLD]
    confident = [outcomes[lang] for lang, rate in rates.items() if rate >= CONFIDENT_THRESHOLD]
    if not trusted:
        return set()
    return {i for i in range(len(trusted[0])) if not any(o[i] for o in trusted) or not all(o[i] for o in confident)}


def differs_only_in_order(expected: Any, actual: Any, mode: str, args: list[Any]) -> bool:
    """A wrong answer under `mode` that is right once list order is ignored at every level."""
    return not judge(expected, actual, mode, args) and judge(expected, actual, "any_order_deep", args)


def _outcomes(
    problem, lang: str, code: str, cases: list[dict], cpp_sig: dict | None, runner_url: str | None
) -> tuple[list[bool], list[bool]]:
    """Per-case pass/fail, and which failures differ only in list order.

    Order-only differences count as passes: they point at a compare mode to curate
    (see `localcode.judging.answer_modes`), not at an invalid input. A case that hangs or crashes
    fails; the cases after it are run again.
    """
    ok = [False] * len(cases)
    order_only = [False] * len(cases)
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
            return [False] * len(cases), order_only
        for i, r in zip(chunk, res["results"], strict=False):
            if not r.get("ok"):
                continue
            expected, args = cases[i]["expected"], cases[i]["args"]
            order_only[i] = differs_only_in_order(expected, r["value"], problem["compare_mode"], args)
            ok[i] = order_only[i] or judge(expected, r["value"], problem["compare_mode"], args)
        done = len(res["results"])
        if done < len(chunk):  # chunk[done] hung or crashed the process; retry what followed it
            pending = chunk[done + 1 :]
    return ok, order_only


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


def _validate_one(slug: str, runner_url: str) -> tuple[list[str], dict[str, str], int]:
    """Case keys to exclude, a pass summary per language, and how many cases differed only in order."""
    p, cases, codes, cpp_sig = _load(slug)
    results = {
        lang: _outcomes(p, lang, codes[lang], cases, cpp_sig if lang == "cpp" else None, runner_url)
        for lang in REFERENCE_LANGS
        if lang in codes and lang in json.loads(p["langs"])
    }
    outcomes = {lang: ok for lang, (ok, _) in results.items()}
    order_only = sum(any(flags) for flags in zip(*(o for _, o in results.values()), strict=True)) if results else 0
    bad = cases_to_exclude(outcomes)
    summary = {k: f"{sum(o)}/{len(o)}" for k, o in outcomes.items()}
    return sorted(case_key(cases[i]["args"]) for i in bad), summary, order_only


def validate(out: Path, only: list[str] | None = None, runners: list[str] | None = None) -> dict[str, list[str]]:
    """Validate every runnable problem, one worker per runner (default: every runner the app can reach).

    Problems whose references differ from the expected answers only in list order are recorded in
    `<out>.order.json` with the number of such cases: candidates for a curated compare mode.
    """
    with content_session() as con:
        slugs = [
            r[0]
            for r in con.execute(
                "select slug from problems where has_tests = 1 order by coalesce(frontend_id, 1000000000), slug"
            )
        ]
    result: dict[str, list[str]] = json.loads(out.read_text()) if out.exists() else {}
    order_out = out.with_suffix(".order.json")
    order: dict[str, int] = json.loads(order_out.read_text()) if order_out.exists() else {}
    todo = [s for s in slugs if s in only] if only else [s for s in slugs if s not in result]
    lock = threading.Lock()
    done = 0
    targets = runners or runner_client.endpoints()
    pool_urls: queue.Queue[str] = queue.Queue()
    for url in targets:
        pool_urls.put(url)

    def work(slug: str) -> None:
        nonlocal done
        url = pool_urls.get()
        try:
            keys, summary, order_only = _validate_one(slug, url)
        finally:
            pool_urls.put(url)
        with lock:
            done += 1
            result[slug] = keys
            out.write_text(json.dumps(result, indent=0, sort_keys=True))
            if order_only:
                order[slug] = order_only
                order_out.write_text(json.dumps(order, indent=0, sort_keys=True))
            note = f", {order_only} differ only in order" if order_only else ""
            print(f"[{done}/{len(todo)}] {slug}: {summary} exclude {len(keys)}{note}", flush=True)

    with ThreadPoolExecutor(max_workers=max(1, len(targets))) as pool:
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
        help="runner endpoints to spread work across (default: every runner socket the app can see)",
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
