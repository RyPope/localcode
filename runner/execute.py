"""Compile and run user code in a throwaway directory as an unprivileged user."""
import json
import os
import resource
import shutil
import signal
import subprocess
import tempfile
import time
from pathlib import Path

HARNESS = Path(__file__).resolve().parent / "harness"
SANDBOX_UID = 10001
MEMORY_BYTES = 512 * 1024 * 1024
COMPILE_TIMEOUT_S = 60
STARTUP_GRACE_MS = {"python": 1000, "cpp": 500, "java": 2000, "kotlin": 2500}
MAX_LOG = 8000


def _limits(memory: bool):
    def apply():
        os.setsid()
        if memory:
            resource.setrlimit(resource.RLIMIT_AS, (MEMORY_BYTES, MEMORY_BYTES))
        resource.setrlimit(resource.RLIMIT_FSIZE, (32 * 1024 * 1024, 32 * 1024 * 1024))
        resource.setrlimit(resource.RLIMIT_STACK, (resource.RLIM_INFINITY, resource.RLIM_INFINITY))
        if os.getuid() == 0:
            os.setgid(SANDBOX_UID)
            os.setuid(SANDBOX_UID)
    return apply


def _spawn(cmd: list[str], cwd: Path, timeout_s: float, memory: bool) -> tuple[int | None, int, bool]:
    """Run cmd; returns (exit status or None if killed for time, maxrss_kb, timed_out)."""
    with open(cwd / "stdout.log", "wb") as so, open(cwd / "stderr.log", "wb") as se:
        proc = subprocess.Popen(cmd, cwd=cwd, stdout=so, stderr=se, stdin=subprocess.DEVNULL,
                                preexec_fn=_limits(memory), env={"PATH": os.environ["PATH"], "HOME": str(cwd),
                                                                  "JAVA_HOME": os.environ.get("JAVA_HOME", "")})
    deadline = time.monotonic() + timeout_s
    while True:
        pid, status, usage = os.wait4(proc.pid, os.WNOHANG)
        if pid:
            proc.returncode = os.waitstatus_to_exitcode(status)
            return proc.returncode, int(usage.ru_maxrss), False
        if time.monotonic() > deadline:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            _, _, usage = os.wait4(proc.pid, 0)
            return None, int(usage.ru_maxrss), True
        time.sleep(0.005)


def _log(path: Path, workdir: Path) -> str:
    text = path.read_text(errors="replace")[-MAX_LOG:] if path.exists() else ""
    return text.replace(str(workdir) + "/", "")


def _compile(cmd: list[str], workdir: Path) -> str | None:
    status, _, timed_out = _spawn(cmd, workdir, COMPILE_TIMEOUT_S, memory=False)
    if timed_out:
        return "Compilation timed out"
    if status != 0:
        return (_log(workdir / "stderr.log", workdir) + _log(workdir / "stdout.log", workdir)).strip() or "Compilation failed"
    return None


def _prepare(lang: str, req: dict, workdir: Path) -> tuple[list[str] | None, list[str], bool]:
    """Write sources; return (compile_cmd, run_cmd, apply_memory_rlimit)."""
    cases, results = "cases.json", "results.jsonl"
    if lang == "python":
        (workdir / "solution.py").write_text(req["code"])
        shutil.copy(HARNESS / "py_driver.py", workdir)
        return None, ["python3", "-I", "py_driver.py", "solution.py", cases, results], True
    if lang == "java":
        (workdir / "Solution.java").write_text(JAVA_IMPORTS + req["code"])
        for f in ("ListNode.java", "TreeNode.java"):
            shutil.copy(HARNESS / "jvm" / f, workdir)
        cp = ".:/opt/lib/gson.jar:/opt/lib/driver.jar"
        return (["javac", "-nowarn", "-encoding", "UTF-8", "-cp", cp, "-d", ".", "Solution.java", "ListNode.java", "TreeNode.java"],
                ["java", "-Xmx384m", "-Xss256m", "-XX:+UseSerialGC", "-XX:TieredStopAtLevel=1", "-cp", cp, "Driver", cases, results], False)
    if lang == "kotlin":
        (workdir / "Solution.kt").write_text(KOTLIN_IMPORTS + req["code"])
        for f in ("ListNode.kt", "TreeNode.kt"):
            shutil.copy(HARNESS / "jvm" / f, workdir)
        cp = ".:/opt/lib/gson.jar:/opt/lib/driver.jar:/opt/kotlinc/lib/kotlin-stdlib.jar"
        return (["kotlinc", "-nowarn", "-d", ".", "Solution.kt", "ListNode.kt", "TreeNode.kt"],
                ["java", "-Xmx384m", "-Xss256m", "-XX:+UseSerialGC", "-cp", cp, "Driver", cases, results], False)
    if lang == "cpp":
        from harness.cpp_gen import gen_main
        (workdir / "main.cpp").write_text(gen_main(req["code"], req["cpp_sig"]))
        return (["g++", "-std=c++20", "-O2", "-w", "-I", "/opt/lc", "-o", "sol", "main.cpp", "/opt/lc/lc_io.o"],
                ["./sol", cases, results], True)
    raise ValueError(f"unknown language {lang!r}")


# Imports share the user's first line so reported line numbers match the editor.
JAVA_IMPORTS = "import java.util.*; import java.util.function.*; import java.util.stream.*; import java.math.*; "
KOTLIN_IMPORTS = "import java.util.*; import kotlin.math.*; "


def execute(req: dict) -> dict:
    lang = req["lang"]
    result = {"compile_error": None, "results": [], "timed_out": False, "memory_kb": 0, "stderr": "", "exit_code": 0}
    workdir = Path(tempfile.mkdtemp(prefix="run-", dir=os.environ.get("RUNNER_TMP", "/tmp")))
    try:
        os.chmod(workdir, 0o777)
        (workdir / "cases.json").write_text(json.dumps(
            {"method": req["method"], "params": req["params"], "ret": req.get("ret"), "cases": req["cases"]}))
        compile_cmd, run_cmd, memory = _prepare(lang, req, workdir)
        if compile_cmd:
            err = _compile(compile_cmd, workdir)
            if err:
                result["compile_error"] = err
                return result
        timeout_s = (req.get("timeout_ms", 10000) + STARTUP_GRACE_MS[lang]) / 1000
        status, rss, timed_out = _spawn(run_cmd, workdir, timeout_s, memory)
        lines = []
        out = workdir / "results.jsonl"
        if out.exists():
            for raw in out.read_text(errors="replace").splitlines():
                try:
                    lines.append(json.loads(raw))
                except json.JSONDecodeError:
                    break
        if lines and "compile_error" in lines[0]:
            result["compile_error"] = lines[0]["compile_error"]
            return result
        result.update(results=lines, timed_out=timed_out, memory_kb=rss, exit_code=status if status is not None else -9,
                      stderr=_log(workdir / "stderr.log", workdir))
        return result
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
