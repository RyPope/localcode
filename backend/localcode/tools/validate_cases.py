"""Maintainer tool: find generated test cases that typed reference solutions reject.

Runs the doocs Java and C++ reference solutions over every problem's suite and records cases that
every *trusted* typed reference fails, or that one *confident* reference fails (see the thresholds).
Those cases almost always violate the problem's constraints: a correct typed solution crashes or
disagrees on them, while another language may get lucky (C++ reads out of bounds without crashing).
The output is our own derived data, shipped as localcode/data/excluded_cases.json and applied by the
importer.

Run inside the app container with `make validate-cases`. It needs the runner and the downloaded sources;
`--from-sources DIR` first builds a content.db in DIR with no cases excluded, so every case is judged:

    docker compose exec -u localcode app python -m localcode.tools.validate_cases \
        --from-sources /data/validate /data/validate/excluded_cases.json
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

from localcode import config, db
from localcode.db import content_session
from localcode.importer.build import MIN_CASES, build_content_db
from localcode.importer.case_filter import case_key
from localcode.judging import runner_client
from localcode.judging.compare import CHECKER_PREFIX, judge

# A reference is trusted when it passes at least TRUST_THRESHOLD of a suite; trusted references that
# agree on a failure exclude the case. A reference passing CONFIDENT_THRESHOLD excludes on its own.
TRUST_THRESHOLD = 0.5
CONFIDENT_THRESHOLD = 0.9
TIMEOUT_MS = 30_000
REFERENCE_LANGS = ("java", "cpp")


def cases_to_exclude(outcomes: dict[str, list[bool]]) -> set[int]:
    """Indices failed by every trusted reference, or by any confident one.

    When every reference (at least two) fails exactly the same cases, those are excluded however many
    there are, as long as MIN_CASES survive: independent implementations agreeing case for case means
    the inputs, not the references, are wrong (suites where most inputs break the constraints).
    """
    present = [o for o in outcomes.values() if o]
    failures = {frozenset(i for i, ok in enumerate(o) if not ok) for o in present}
    if len(present) >= 2 and len(failures) == 1:
        (agreed,) = failures
        if len(present[0]) - len(agreed) >= MIN_CASES:
            return set(agreed)
    rates = {lang: sum(o) / len(o) for lang, o in outcomes.items() if o}
    trusted = [outcomes[lang] for lang, rate in rates.items() if rate >= TRUST_THRESHOLD]
    confident = [outcomes[lang] for lang, rate in rates.items() if rate >= CONFIDENT_THRESHOLD]
    if not trusted:
        return set()
    return {i for i in range(len(trusted[0])) if not any(o[i] for o in trusted) or not all(o[i] for o in confident)}


def needs_review(outcomes: dict[str, list[bool]]) -> bool:
    """Cases are excluded although no reference passes TRUST_THRESHOLD of the suite (agreement only).

    References are often translations of one algorithm and can share a bug or a limit, so these
    exclusions are listed for a person to confirm that the inputs really break the constraints.
    """
    rates = [sum(o) / len(o) for o in outcomes.values() if o]
    return bool(cases_to_exclude(outcomes)) and max(rates, default=0) < TRUST_THRESHOLD


def differs_only_in_order(expected: Any, actual: Any, mode: str, args: list[Any]) -> bool:
    """A wrong answer under `mode` that is right once list order is ignored at every level.

    Never true for a checker: it already accepts every valid ordering, so its rejections are real.
    """
    if mode.startswith(CHECKER_PREFIX):
        return False
    return not judge(expected, actual, mode, args) and judge(expected, actual, "any_order_deep", args)


def _outcomes(
    problem, lang: str, code: str, cases: list[dict], cpp_sig: dict | None, runner_url: str | None
) -> tuple[list[bool], list[bool]]:
    """Per-case pass/fail, and which failures differ only in list order.

    Order-only differences still fail (an invalid input can look like a reordering), but are reported
    so the problem's compare mode can be reviewed in `localcode.judging.answer_modes`. A case that hangs
    or crashes fails; the cases after it are run again.
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
            ok[i] = judge(expected, r["value"], problem["compare_mode"], args)
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


def _validate_one(slug: str, runner_url: str) -> tuple[list[str], dict[str, str], int, bool]:
    """Case keys to exclude, a pass summary per language, how many cases differed only in order, and
    whether the exclusions need review."""
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
    return sorted(case_key(cases[i]["args"]) for i in bad), summary, order_only, needs_review(outcomes)


def prepare_from_sources(sources: Path, work: Path) -> None:
    """Build `work/content.db` from `sources` with nothing excluded, and judge against it."""
    work.mkdir(parents=True, exist_ok=True)
    (work / "content.db").unlink(missing_ok=True)  # nothing may be carried forward from an older build
    build_content_db(sources, work / "content.db", lambda *a: None, excluded={})
    db.CONTENT_DB, db.USER_DB = work / "content.db", work / "user.db"


class _Report:
    """A JSON object of slug -> finding, rewritten on every change; re-validating a slug replaces it."""

    def __init__(self, path: Path, keep: bool) -> None:
        self.path = path
        self.data: dict[str, object] = json.loads(path.read_text()) if keep and path.exists() else {}
        self._write()

    def record(self, slug: str, finding: object | None) -> None:
        if finding is None and slug not in self.data:
            return
        if finding is None:
            del self.data[slug]
        else:
            self.data[slug] = finding
        self._write()

    def _write(self) -> None:
        self.path.write_text(json.dumps(self.data, indent=0, sort_keys=True))


def _case_count(summary: dict[str, str]) -> int:
    return max((int(s.split("/")[1]) for s in summary.values()), default=0)


def _runnable_slugs() -> list[str]:
    with content_session() as con:
        rows = con.execute(
            "select slug from problems where has_tests = 1 order by coalesce(frontend_id, 1000000000), slug"
        )
        return [r[0] for r in rows]


def validate(
    out: Path, only: list[str] | None = None, runners: list[str] | None = None, *, fresh: bool = False
) -> dict[str, list[str]]:
    """Validate every runnable problem, one worker per runner (default: every runner the app can reach).

    Resumes from `out` unless `fresh`; with `only`, re-validates those problems and keeps the rest.

    Two reports sit next to `out`, for a person to act on:
    - `<out>.order.json`: problems whose references differ from the expected answers only in list
      order, with the number of such cases. Give each a compare mode, then re-run it with `--only`.
    - `<out>.review.json`: problems whose exclusions rest on references agreeing although none passes
      half the suite (see `needs_review`), as `[excluded, total]`. Confirm the inputs are invalid.
    """
    slugs = _runnable_slugs()
    keep = not fresh
    result: dict[str, list[str]] = json.loads(out.read_text()) if keep and out.exists() else {}
    reports = {name: _Report(out.with_suffix(f".{name}.json"), keep) for name in ("order", "review")}
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
            keys, summary, order_only, review = _validate_one(slug, url)
        finally:
            pool_urls.put(url)
        with lock:
            done += 1
            result[slug] = keys
            out.write_text(json.dumps(result, indent=0, sort_keys=True))
            reports["order"].record(slug, order_only or None)
            reports["review"].record(slug, [len(keys), _case_count(summary)] if review else None)
            note = f", {order_only} differ only in order" if order_only else ""
            note += ", needs review" if review else ""
            print(f"[{done}/{len(todo)}] {slug}: {summary} exclude {len(keys)}{note}", flush=True)

    with ThreadPoolExecutor(max_workers=max(1, len(targets))) as pool:
        for f in [pool.submit(work, s) for s in todo]:
            f.result()
    return result


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("out", type=Path, help="JSON file to write (resumes if it exists, unless --from-sources)")
    ap.add_argument(
        "--from-sources",
        type=Path,
        metavar="DIR",
        help="first build an unfiltered content.db in DIR from the downloaded sources and start a fresh list",
    )
    ap.add_argument("--only", nargs="*", help="limit to these problem slugs")
    ap.add_argument(
        "--runners",
        nargs="*",
        help="runner endpoints to spread work across (default: every runner socket the app can see)",
    )
    args = ap.parse_args(argv)
    if args.from_sources:
        prepare_from_sources(config.SOURCES_DIR, args.from_sources)
    t0 = time.time()
    result = validate(args.out, args.only, args.runners, fresh=bool(args.from_sources and not args.only))
    print(
        f"done: {sum(map(len, result.values()))} cases excluded across {len(result)} problems "
        f"in {time.time() - t0:.0f}s",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
