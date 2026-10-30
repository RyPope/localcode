"""Compile and run one submission against a batch of cases, returning raw per-case results."""

import json
import shutil
from pathlib import Path

import sandbox
from languages import CASES, LANGUAGES, RESULTS

COMPILE_TIMEOUT_S = 60
DEFAULT_MEMORY_MB = 1024
MAX_MEMORY_MB = 2048  # the app chooses the limit; this only guards against absurd requests
MAX_LOG = 8000


def _log(path: Path, workdir: Path) -> str:
    text = path.read_text(errors="replace")[-MAX_LOG:] if path.exists() else ""
    return text.replace(str(workdir) + "/", "")


def _compile(cmd: list[str], workdir: Path) -> str | None:
    """Compiler output on failure, else None."""
    outcome = sandbox.spawn(cmd, workdir, COMPILE_TIMEOUT_S)
    if outcome.timed_out:
        return "Compilation timed out"
    if outcome.exit_code != 0:
        output = _log(workdir / "stderr.log", workdir) + _log(workdir / "stdout.log", workdir)
        return output.strip() or "Compilation failed"
    return None


def _read_results(path: Path) -> list[dict]:
    """Complete JSON lines only: a process killed mid-write leaves a partial last line."""
    lines: list[dict] = []
    if path.exists():
        for raw in path.read_text(errors="replace").splitlines():
            try:
                lines.append(json.loads(raw))
            except json.JSONDecodeError:
                break
    return lines


def execute(req: dict) -> dict:
    language = LANGUAGES.get(req["lang"])
    if language is None:
        raise ValueError(f"unknown language {req['lang']!r}")
    memory_mb = min(int(req.get("memory_mb", DEFAULT_MEMORY_MB)), MAX_MEMORY_MB)
    result = {"compile_error": None, "results": [], "timed_out": False, "memory_kb": 0, "stderr": "", "exit_code": 0}
    workdir = sandbox.make_workdir()
    try:
        spec = {"method": req["method"], "params": req["params"], "ret": req.get("ret"), "cases": req["cases"]}
        (workdir / CASES).write_text(json.dumps(spec))
        plan = language.prepare(req, workdir, memory_mb)
        if plan.compile and (error := _compile(plan.compile, workdir)):
            result["compile_error"] = error
            return result

        timeout_s = (req.get("timeout_ms", 10_000) + language.startup_grace_ms) / 1000
        address_space = memory_mb * 1024 * 1024 if plan.limit_address_space else None
        outcome = sandbox.spawn(plan.run, workdir, timeout_s, address_space)
        lines = _read_results(workdir / RESULTS)
        if lines and "compile_error" in lines[0]:  # e.g. a Python syntax error, detected by the harness
            result["compile_error"] = lines[0]["compile_error"]
            return result
        result.update(
            results=lines,
            timed_out=outcome.timed_out,
            memory_kb=outcome.max_rss_kb,
            exit_code=outcome.exit_code if outcome.exit_code is not None else -9,
            stderr=_log(workdir / "stderr.log", workdir),
        )
        return result
    finally:
        sandbox.reap()
        shutil.rmtree(workdir, ignore_errors=True)
