"""Isolation between submissions: identity, process limits, and cleanup after each run."""

INT = [{"name": "x", "type": "int"}]


def py(body: str) -> str:
    lines = "\n".join("        " + line for line in body.strip().splitlines())
    return f"import os, time, signal\nclass Solution:\n    def f(self, x: int) -> int:\n{lines}\n"


def value(r):
    assert r["compile_error"] is None, r
    assert r["results"] and r["results"][0]["ok"], r
    return r["results"][0]["value"]


def test_no_supplementary_root_group(run):
    assert value(run("python", py("return int(0 in os.getgroups())"), "f", INT, [[1]])) == 0


def test_workdir_is_private_to_the_sandbox_user(run):
    code = py("st = os.stat('.')\nreturn int(st.st_uid == os.getuid() and (st.st_mode & 0o777) == 0o700)")
    assert value(run("python", code, "f", INT, [[1]])) == 1


def test_stray_processes_are_killed_between_runs(run):
    spawn = py("""
if os.fork() == 0:
    os.setsid()
    time.sleep(60)
    os._exit(0)
return 1
""")
    assert value(run("python", spawn, "f", INT, [[1]])) == 1
    count = py("""
mine = 0
for pid in filter(str.isdigit, os.listdir('/proc')):
    try:
        with open(f'/proc/{pid}/status') as fh:
            uid = next(int(l.split()[1]) for l in fh if l.startswith('Uid:'))
    except (OSError, StopIteration):
        continue
    mine += uid == os.getuid()
return mine
""")
    assert value(run("python", count, "f", INT, [[1]])) == 1  # only this run's own process


def test_tmp_files_do_not_survive_a_run(run):
    assert value(run("python", py("open('/tmp/leftover', 'w').write('x')\nreturn 1"), "f", INT, [[1]])) == 1
    assert value(run("python", py("return int(os.path.exists('/tmp/leftover'))"), "f", INT, [[1]])) == 0


def test_fork_bomb_is_capped_and_runner_recovers(run):
    bomb = py("""
n = 0
for _ in range(2000):
    try:
        if os.fork() == 0:
            time.sleep(30)
            os._exit(0)
        n += 1
    except OSError:
        break
return n
""")
    started = value(run("python", bomb, "f", INT, [[1]]))
    assert started < 512
    assert value(run("python", py("return x + 1"), "f", INT, [[41]])) == 42


def test_memory_limit_comes_from_the_request(url):
    import json
    import urllib.request

    code = py("a = bytearray(400 * 1024 * 1024)\nreturn 1")
    body = {
        "lang": "python",
        "code": code,
        "method": "f",
        "params": INT,
        "ret": "int",
        "cases": [[1]],
        "timeout_ms": 5000,
        "cpp_sig": None,
        "memory_mb": 256,
    }
    req = urllib.request.Request(url + "/execute", json.dumps(body).encode(), {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        res = json.load(r)
    assert res["results"][0]["ok"] is False
    assert "MemoryError" in res["results"][0]["error"]


def test_shared_memory_does_not_survive_a_run(run):
    assert value(run("python", py("open('/dev/shm/leftover', 'w').write('x')\nreturn 1"), "f", INT, [[1]])) == 1
    assert value(run("python", py("return int(os.path.exists('/dev/shm/leftover'))"), "f", INT, [[1]])) == 0


IPC_SETUP = """
import ctypes
libc = ctypes.CDLL(None, use_errno=True)
IPC_PRIVATE, IPC_CREAT = 0, 0o1000
"""


def test_ipc_objects_do_not_survive_a_run(run):
    create = py(
        IPC_SETUP
        + """
ok = libc.shmget(IPC_PRIVATE, 4096, IPC_CREAT | 0o600) >= 0
ok &= libc.msgget(IPC_PRIVATE, IPC_CREAT | 0o600) >= 0
ok &= libc.semget(IPC_PRIVATE, 1, IPC_CREAT | 0o600) >= 0
ok &= libc.mq_open(b"/leftover", os.O_CREAT | os.O_RDWR, 0o600, None) >= 0
return int(ok)
"""
    )
    assert value(run("python", create, "f", INT, [[1]])) == 1
    count = py("""
mine = 0
for kind in ("shm", "msg", "sem"):
    with open(f"/proc/sysvipc/{kind}") as fh:
        header = fh.readline().split()
        uid = header.index("uid")
        mine += sum(int(line.split()[uid]) == os.getuid() for line in fh)
return mine + len(os.listdir("/dev/mqueue"))
""")
    assert value(run("python", count, "f", INT, [[1]])) == 0


def test_shared_memory_segments_are_size_capped(run):
    big = py(IPC_SETUP + "return int(libc.shmget(IPC_PRIVATE, 64 * 1024 * 1024, IPC_CREAT | 0o600) >= 0)")
    assert value(run("python", big, "f", INT, [[1]])) == 0


def test_stderr_is_captured(run):
    r = run("python", py("import sys\nprint('to stderr', file=sys.stderr)\nreturn 1"), "f", INT, [[1]])
    assert value(r) == 1
    assert "to stderr" in r["stderr"]


def test_replacing_a_log_with_a_symlink_cannot_read_root_files(run):
    swap = py("""
for name in ("stderr.log", "stdout.log"):
    if os.path.lexists(name):
        os.unlink(name)
    os.symlink("/etc/shadow", name)
return 1
""")
    r = run("python", swap, "f", INT, [[1]])
    assert "root:" not in r["stderr"]


def test_results_are_not_read_through_a_symlink(tmp_path):
    import os
    import shutil

    import execute
    import sandbox

    secret = tmp_path / "secret.jsonl"
    secret.write_text('{"ok": true, "value": "secret"}\n')
    os.chmod(secret, 0o600)
    workdir = sandbox.make_workdir()
    try:
        (workdir / "results.jsonl").symlink_to(secret)
        assert execute._read_results(workdir / "results.jsonl") == []
    finally:
        shutil.rmtree(workdir)
