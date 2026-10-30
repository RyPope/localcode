"""Pure grading: turn a runner result plus expected values into Run/Submit verdicts. No I/O."""

from dataclasses import asdict, dataclass, field
from typing import Any

from localcode.judging.compare import judge
from localcode.judging.types import Case, RunnerResult

ACCEPTED = "Accepted"
WRONG_ANSWER = "Wrong Answer"
RUNTIME_ERROR = "Runtime Error"
TIME_LIMIT = "Time Limit Exceeded"
MEMORY_LIMIT = "Memory Limit Exceeded"
COMPILE_ERROR = "Compile Error"

_MEMORY_MARKERS = ("MemoryError", "OutOfMemoryError", "bad_alloc")
_SIGNALS = {
    -11: "Segmentation fault (SIGSEGV)",
    -6: "Aborted (SIGABRT)",
    -8: "Floating point exception (SIGFPE)",
    -7: "Bus error (SIGBUS)",
}
NO_REFERENCE = "Reference solution could not run this input"


def case_failure(res: RunnerResult, i: int) -> tuple[str, str | None]:
    """Verdict and error text for case `i`, which did not produce a clean result."""
    if i < len(res["results"]):
        err = res["results"][i].get("error") or ""
        return (MEMORY_LIMIT if any(m in err for m in _MEMORY_MARKERS) else RUNTIME_ERROR), err
    if res["timed_out"]:
        return TIME_LIMIT, None
    code = res.get("exit_code", 0)
    if code == -9:
        return MEMORY_LIMIT, "Process was killed (out of memory)"
    detail = _SIGNALS.get(code, f"Process exited with code {code}")
    stderr = (res.get("stderr") or "").strip()
    return RUNTIME_ERROR, detail + (f"\n{stderr[-2000:]}" if stderr else "")


@dataclass
class RunCase:
    args: list[Any]
    expected: Any
    actual: Any
    stdout: str
    ok: bool
    error: str | None
    ms: float | None


@dataclass
class RunGrade:
    verdict: str
    compile_error: str | None = None
    cases: list[RunCase] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def grade_run(arg_lists: list[list[Any]], expected: list[Any], res: RunnerResult, mode: str) -> RunGrade:
    """Every case is reported; the verdict is the first problem found (or Accepted)."""
    if res["compile_error"]:
        return RunGrade(COMPILE_ERROR, res["compile_error"])
    grade = RunGrade(ACCEPTED)
    for i, (args, exp) in enumerate(zip(arg_lists, expected, strict=False)):
        r = res["results"][i] if i < len(res["results"]) else None
        if r and r.get("ok"):
            passed = exp is not None and judge(exp, r["value"], mode)
            grade.cases.append(
                RunCase(
                    args,
                    exp,
                    r["value"],
                    r.get("stdout", ""),
                    passed,
                    None if exp is not None else NO_REFERENCE,
                    r.get("ms"),
                )
            )
            kind = WRONG_ANSWER
        else:
            kind, err = case_failure(res, i)
            grade.cases.append(RunCase(args, exp, None, r.get("stdout", "") if r else "", False, err, None))
            passed = False
        if not passed and grade.verdict == ACCEPTED:
            grade.verdict = kind
    return grade


@dataclass
class SubmitGrade:
    verdict: str
    passed: int
    total: int
    runtime_ms: float | None
    memory_kb: int
    failing: dict | None
    compile_error: str | None

    def to_dict(self) -> dict:
        return asdict(self)


def grade_submission(cases: list[Case], res: RunnerResult, mode: str) -> SubmitGrade:
    """Stops at the first failing case, as LeetCode does."""
    grade = SubmitGrade(ACCEPTED, 0, len(cases), None, res["memory_kb"], None, res["compile_error"])
    if res["compile_error"]:
        grade.verdict = COMPILE_ERROR
        return grade
    for i, case in enumerate(cases):
        r = res["results"][i] if i < len(res["results"]) else None
        if r and r.get("ok") and judge(case["expected"], r["value"], mode):
            grade.passed += 1
            continue
        if r and r.get("ok"):
            grade.verdict, err = WRONG_ANSWER, None
        else:
            grade.verdict, err = case_failure(res, i)
        grade.failing = {
            "args": case["args"],
            "expected": case["expected"],
            "actual": r["value"] if r and r.get("ok") else None,
            "stdout": r.get("stdout", "") if r else "",
            "error": err,
        }
        return grade
    grade.runtime_ms = round(sum(r.get("ms") or 0 for r in res["results"]), 3)
    return grade
