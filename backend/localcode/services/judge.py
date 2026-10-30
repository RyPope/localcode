"""Run and Submit: build runner requests, compute expected values, grade, and record submissions."""

import json
import sqlite3
import threading
from collections import OrderedDict
from collections.abc import Callable, Mapping
from typing import Any

from localcode import config
from localcode.db import content_session
from localcode.judging.kwargs import parse_kwargs
from localcode.judging.runner_client import RunnerUnavailable
from localcode.judging.types import RunnerRequest, RunnerResult
from localcode.judging.verdicts import grade_run, grade_submission
from localcode.services import progress
from localcode.services.errors import ServiceError, bad_request
from localcode.services.problems import content_version, load_problem

Runner = Callable[[RunnerRequest], RunnerResult]


class ExpectedCache:
    """Reference outputs for Run inputs, computed by running the Python reference solution.

    Keyed by content version as well as (slug, args), so a re-import invalidates entries without the
    importer knowing this cache exists. Least-recently-used entries are evicted beyond `max_entries`.
    """

    def __init__(self, max_entries: int = 10_000) -> None:
        self._values: OrderedDict[tuple[str, str, str], Any] = OrderedDict()
        self._max = max_entries
        self._lock = threading.Lock()

    def __len__(self) -> int:
        return len(self._values)

    def resolve(
        self, runner: Runner, problem: Mapping[str, Any], arg_lists: list[list[Any]], version: str
    ) -> list[Any]:
        keys = [(version, problem["slug"], json.dumps(a)) for a in arg_lists]
        with self._lock:
            missing = [a for a, k in zip(arg_lists, keys, strict=True) if k not in self._values]
        if missing:
            timeout = config.LIMITS.run_per_case_ms * len(missing)
            res = _execute(runner, _request(problem, "python", problem["ref_python"], missing, timeout))
            with self._lock:
                for args, r in zip(missing, res["results"], strict=False):
                    if r.get("ok"):
                        self._values[(version, problem["slug"], json.dumps(args))] = r["value"]
        with self._lock:
            out = []
            for k in keys:
                if k in self._values:
                    self._values.move_to_end(k)
                out.append(self._values.get(k))
            while len(self._values) > self._max:
                self._values.popitem(last=False)
            return out

    def clear(self) -> None:
        with self._lock:
            self._values.clear()


expected_cache = ExpectedCache()


def _execute(runner: Runner, req: RunnerRequest) -> RunnerResult:
    try:
        return runner(req)
    except RunnerUnavailable as e:
        raise ServiceError(503, f"Code runner unavailable ({e}). Is the runner container up?") from e


def _request(
    p: Mapping[str, Any], lang: str, code: str, cases: list[list[Any]], timeout_ms: int, cpp_sig: dict | None = None
) -> RunnerRequest:
    return {
        "lang": lang,
        "code": code,
        "method": p["method"],
        "params": json.loads(p["params"]),
        "ret": p["ret"],
        "cases": cases,
        "timeout_ms": timeout_ms,
        "memory_mb": config.LIMITS.memory_mb,
        "cpp_sig": cpp_sig,
    }


def _cpp_sig(con: sqlite3.Connection, slug: str, lang: str) -> dict | None:
    if lang != "cpp":
        return None
    return json.loads(
        con.execute("select cpp_sig from starters where slug = ? and lang = 'cpp'", (slug,)).fetchone()[0]
    )


def _check_runnable(p: sqlite3.Row, lang: str) -> None:
    if not p["has_tests"]:
        raise bad_request("No tests available for this problem")
    if lang not in json.loads(p["langs"]):
        raise bad_request(f"{lang} is not available for this problem")


def parse_custom_cases(p: sqlite3.Row, custom: list[str]) -> list[list[Any]]:
    """`name = value, …` strings → positional argument lists, validated against the signature."""
    names = [x["name"] for x in json.loads(p["params"])]
    out = []
    for i, text in enumerate(custom, 1):
        try:
            kw = parse_kwargs(text)
        except ValueError as e:
            raise bad_request(f"Custom case {i}: {e}") from e
        if set(kw) != set(names):
            raise bad_request(f"Custom case {i} must set exactly: {', '.join(names)}")
        out.append([kw[n] for n in names])
    return out


def run(runner: Runner, slug: str, lang: str, code: str, custom: list[str] | None = None) -> dict:
    with content_session() as con:
        p = load_problem(con, slug)
        _check_runnable(p, lang)
        cpp_sig = _cpp_sig(con, slug, lang)
        version = content_version(con)
    arg_lists = json.loads(p["examples"]) + parse_custom_cases(p, custom or [])
    expected = expected_cache.resolve(runner, p, arg_lists, version)
    res = _execute(runner, _request(p, lang, code, arg_lists, config.LIMITS.run_per_case_ms * len(arg_lists), cpp_sig))
    return grade_run(arg_lists, expected, res, p["compare_mode"]).to_dict()


def submit(runner: Runner, slug: str, lang: str, code: str) -> dict:
    with content_session() as con:
        p = load_problem(con, slug)
        _check_runnable(p, lang)
        cpp_sig = _cpp_sig(con, slug, lang)
        cases = json.loads(con.execute("select cases from tests where slug = ?", (slug,)).fetchone()[0])
    res = _execute(runner, _request(p, lang, code, [c["args"] for c in cases], config.LIMITS.submit_total_ms, cpp_sig))
    grade = grade_submission(cases, res, p["compare_mode"]).to_dict()
    grade["submission_id"] = progress.record_submission(slug, lang, code, grade)
    return grade
