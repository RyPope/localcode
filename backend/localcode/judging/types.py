"""Wire types shared by the app and the runner service."""

from typing import Any, TypedDict


class Param(TypedDict):
    name: str
    type: str  # abstract type from the Python signature: int, str, List[int], TreeNode, ...


class Case(TypedDict):
    args: list[Any]
    expected: Any


class CaseResult(TypedDict, total=False):
    ok: bool
    value: Any
    error: str | None
    stdout: str
    ms: float


class RunnerRequest(TypedDict):
    lang: str
    code: str
    method: str
    params: list[Param]
    ret: str | None
    cases: list[list[Any]]
    timeout_ms: int
    memory_mb: int
    cpp_sig: dict | None


class RunnerResult(TypedDict):
    compile_error: str | None
    results: list[CaseResult]
    timed_out: bool
    memory_kb: int
    exit_code: int
    stderr: str
