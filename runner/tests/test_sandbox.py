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
