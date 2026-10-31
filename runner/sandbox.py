"""Process isolation for submissions: an unprivileged user, resource limits, and cleanup between runs."""

import contextlib
import os
import resource
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

SANDBOX_UID = 10001
MAX_PROCESSES = 256  # per sandbox user; JVM threads count towards it
MAX_FILE_BYTES = 32 * 1024 * 1024
LOG_TAIL_BYTES = 64 * 1024
TMP_ROOT = Path(os.environ.get("RUNNER_TMP", "/tmp"))
# Every location the sandbox user can write to; all are emptied of its files after each run.
WRITABLE_DIRS = (TMP_ROOT, Path("/dev/shm"), Path("/dev/mqueue"))


@dataclass(frozen=True)
class Outcome:
    exit_code: int | None  # None when killed for exceeding the time limit
    max_rss_kb: int
    timed_out: bool
    stdout: str
    stderr: str


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


def _tail(log) -> str:
    size = log.seek(0, os.SEEK_END)
    log.seek(max(0, size - LOG_TAIL_BYTES))
    return log.read().decode(errors="replace")


def spawn(cmd: list[str], cwd: Path, timeout_s: float, address_space_bytes: int | None = None) -> Outcome:
    """Run `cmd` as the sandbox user, capturing the tail of its stdout and stderr.

    Output goes to unlinked files the runner holds open, so the submission has no path it could
    swap for a link to a file only root can read.
    """
    with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
        proc = subprocess.Popen(
            cmd,
            cwd=cwd,
            stdout=out,
            stderr=err,
            stdin=subprocess.DEVNULL,
            preexec_fn=_drop_privileges(address_space_bytes),
            env={"PATH": os.environ["PATH"], "HOME": str(cwd), "JAVA_HOME": os.environ.get("JAVA_HOME", "")},
        )
        exit_code, max_rss_kb, timed_out = _wait(proc, timeout_s)
        return Outcome(exit_code, max_rss_kb, timed_out, _tail(out), _tail(err))


def _wait(proc: subprocess.Popen, timeout_s: float) -> tuple[int | None, int, bool]:
    deadline = time.monotonic() + timeout_s
    while True:
        pid, status, usage = os.wait4(proc.pid, os.WNOHANG)
        if pid:
            return os.waitstatus_to_exitcode(status), int(usage.ru_maxrss), False
        if time.monotonic() > deadline:
            with contextlib.suppress(ProcessLookupError):
                os.killpg(proc.pid, signal.SIGKILL)
            _, _, usage = os.wait4(proc.pid, 0)
            return None, int(usage.ru_maxrss), True
        time.sleep(0.005)


def read_output(path: Path) -> str:
    """A file the submission wrote, or "" if it is missing or isn't a regular file the sandbox user owns.

    Refuses links and anything else the submission could point at a file only root can read.
    """
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except OSError:
        return ""
    with os.fdopen(fd, "rb") as fh:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode) or (is_sandboxed() and st.st_uid != SANDBOX_UID):
            return ""
        return fh.read().decode(errors="replace")


def make_workdir() -> Path:
    """A fresh directory only the sandbox user can enter."""
    workdir = Path(tempfile.mkdtemp(prefix="run-", dir=TMP_ROOT))
    if is_sandboxed():
        os.chown(workdir, SANDBOX_UID, SANDBOX_UID)
    os.chmod(workdir, 0o700)
    return workdir


# Run as the sandbox user: kill(-1) reaches exactly its processes (repeated in case a fork bomb
# respawns), and only an IPC object's owner may remove it without CAP_SYS_ADMIN.
_CLEAN_UP = """
import contextlib, ctypes, os, signal
for _ in range(3):
    with contextlib.suppress(ProcessLookupError):
        os.kill(-1, signal.SIGKILL)
libc = ctypes.CDLL(None)
IPC_RMID = 0
remove = {
    "shm": lambda i: libc.shmctl(i, IPC_RMID, None),
    "msg": lambda i: libc.msgctl(i, IPC_RMID, None),
    "sem": lambda i: libc.semctl(i, 0, IPC_RMID),
}
for kind, rm in remove.items():
    with contextlib.suppress(OSError), open(f"/proc/sysvipc/{kind}") as fh:
        uid = fh.readline().split().index("uid")
        for line in fh:
            fields = line.split()
            if int(fields[uid]) == os.getuid():
                rm(int(fields[1]))
"""


def reap() -> None:
    """Kill every process the sandbox user still owns and delete its IPC objects and its files in WRITABLE_DIRS.

    Executions are serialised, so anything left belongs to a finished run (background children,
    setsid'd daemons, fork bombs, shared memory, message queues) and must not leak into the next one.
    """
    if not is_sandboxed():
        return
    subprocess.run(
        [sys.executable, "-I", "-c", _CLEAN_UP],
        user=SANDBOX_UID,
        group=SANDBOX_UID,
        extra_groups=[],
        check=False,
        timeout=10,
    )
    for directory in WRITABLE_DIRS:
        for entry in directory.iterdir() if directory.is_dir() else ():
            with contextlib.suppress(OSError):
                if entry.lstat().st_uid == SANDBOX_UID:
                    if entry.is_dir() and not entry.is_symlink():
                        shutil.rmtree(entry, ignore_errors=True)
                    else:
                        entry.unlink()
