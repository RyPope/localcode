import json
import shutil
import socketserver
import tempfile
import threading
from http.server import BaseHTTPRequestHandler
from pathlib import Path

import pytest

from localcode import config
from localcode.judging import runner_client
from localcode.judging.runner_client import RunnerUnavailable

REQ = {
    "lang": "python",
    "code": "",
    "method": "f",
    "params": [],
    "ret": None,
    "cases": [],
    "timeout_ms": 1000,
    "memory_mb": 64,
    "cpp_sig": None,
}


class _Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        self.rfile.read(int(self.headers["Content-Length"]))
        body = json.dumps(
            {
                "compile_error": None,
                "results": [],
                "timed_out": False,
                "memory_kb": 1,
                "exit_code": 0,
                "stderr": "",
                "served_by": self.server.name,
            }
        ).encode()
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


def serve_unix(path, name="live"):
    server = socketserver.ThreadingUnixStreamServer(str(path), _Handler)
    server.name = name
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


@pytest.fixture
def sockets(monkeypatch):
    # Unix socket paths are limited to ~104 bytes on macOS, so avoid pytest's long tmp_path.
    directory = Path(tempfile.mkdtemp(prefix="lc-", dir="/tmp"))
    monkeypatch.setattr(config, "RUNNER_URL", f"unix:{directory}")
    yield directory
    shutil.rmtree(directory, ignore_errors=True)


def test_endpoints_discovers_runner_sockets(sockets):
    (sockets / "runner-a.sock").touch()
    (sockets / "runner-b.sock").touch()
    (sockets / "unrelated.txt").touch()
    assert runner_client.endpoints() == [f"unix:{sockets}/runner-a.sock", f"unix:{sockets}/runner-b.sock"]


def test_http_url_is_used_as_is(monkeypatch):
    monkeypatch.setattr(config, "RUNNER_URL", "http://runner:8080")
    assert runner_client.endpoints() == ["http://runner:8080"]


def test_execute_over_unix_socket_skips_stale_sockets(sockets):
    (sockets / "runner-dead.sock").touch()  # left behind by a stopped replica
    server = serve_unix(sockets / "runner-live.sock")
    try:
        assert runner_client.execute(REQ)["served_by"] == "live"
    finally:
        server.shutdown()


def test_no_runner_is_unavailable(sockets):
    with pytest.raises(RunnerUnavailable, match="no runner"):
        runner_client.execute(REQ)
