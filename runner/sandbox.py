"""Process isolation for submissions: an unprivileged user, resource limits, and cleanup between runs."""

import contextlib
import os
import resource
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

SANDBOX_UID = 10001
MAX_PROCESSES = 256  # per sandbox user; JVM threads count towards it
MAX_FILE_BYTES = 32 * 1024 * 1024
TMP_ROOT = Path(os.environ.get("RUNNER_TMP", "/tmp"))


@dataclass(frozen=True)
class Outcome:
    exit_code: int | None  # None when killed for exceeding the time limit
    max_rss_kb: int
    timed_out: bool


def is_sandboxed() -> bool:
    """True when running as root, i.e. able to drop to the sandbox user (always, inside the container)."""
    return os.getuid() == 0


def _drop_privileges(address_space_bytes: int | None):
    def apply() -> None:
        os.setsid()
        if address_space_bytes:
            resource.setrlimit(resource.RLIMIT_AS, (address_space_bytes, address_space_bytes))
        resource.setrlimit(resource.RLIMIT_FSIZE, (MAX_FILE_BYTES, MAX_FILE_BYTES))
        resource.setrlimit(resource.RLIMIT_STACK, (resource.RLIM_INFINITY, resource.RLIM_INFINITY))
        if is_sandboxed():
            resource.setrlimit(resource.RLIMIT_NPROC, (MAX_PROCESSES, MAX_PROCESSES))
            os.setgroups([])
            os.setgid(SANDBOX_UID)
            os.setuid(SANDBOX_UID)

    return apply


def spawn(cmd: list[str], cwd: Path, timeout_s: float, address_space_bytes: int | None = None) -> Outcome:
    """Run `cmd` as the sandbox user with stdout/stderr in cwd/{stdout,stderr}.log."""
    with open(cwd / "stdout.log", "wb") as out, open(cwd / "stderr.log", "wb") as err:
        proc = subprocess.Popen(
            cmd,
            cwd=cwd,
            stdout=out,
            stderr=err,
            stdin=subprocess.DEVNULL,
            preexec_fn=_drop_privileges(address_space_bytes),
            env={"PATH": os.environ["PATH"], "HOME": str(cwd), "JAVA_HOME": os.environ.get("JAVA_HOME", "")},
        )
    deadline = time.monotonic() + timeout_s
    while True:
        pid, status, usage = os.wait4(proc.pid, os.WNOHANG)
        if pid:
            return Outcome(os.waitstatus_to_exitcode(status), int(usage.ru_maxrss), False)
        if time.monotonic() > deadline:
            with contextlib.suppress(ProcessLookupError):
                os.killpg(proc.pid, signal.SIGKILL)
            _, _, usage = os.wait4(proc.pid, 0)
            return Outcome(None, int(usage.ru_maxrss), True)
        time.sleep(0.005)


def make_workdir() -> Path:
    """A fresh directory only the sandbox user can enter."""
    workdir = Path(tempfile.mkdtemp(prefix="run-", dir=TMP_ROOT))
    if is_sandboxed():
        os.chown(workdir, SANDBOX_UID, SANDBOX_UID)
    os.chmod(workdir, 0o700)
    return workdir


_KILL_ALL = """
import contextlib, os, signal
for _ in range(3):
    with contextlib.suppress(ProcessLookupError):
        os.kill(-1, signal.SIGKILL)
"""


def reap() -> None:
    """Kill every process the sandbox user still owns and delete its files in TMP_ROOT.

    Executions are serialised, so anything left belongs to a finished run (background children,
    setsid'd daemons, fork bombs) and must not leak into the next one.
    """
    if not is_sandboxed():
        return
    # As the sandbox user, kill(-1) reaches exactly its processes; repeat in case a fork bomb respawns.
    subprocess.run(
        [sys.executable, "-I", "-c", _KILL_ALL],
        user=SANDBOX_UID,
        group=SANDBOX_UID,
        extra_groups=[],
        check=False,
        timeout=10,
    )
    for entry in TMP_ROOT.iterdir():
        with contextlib.suppress(OSError):
            if entry.lstat().st_uid == SANDBOX_UID:
                if entry.is_dir() and not entry.is_symlink():
                    shutil.rmtree(entry, ignore_errors=True)
                else:
                    entry.unlink()
