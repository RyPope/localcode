"""HTTP front for execute(): POST /execute, GET /health. One execution at a time.

In Docker the runner has no network: it serves on a Unix socket in RUNNER_SOCKET_DIR that only the
app's group can open (the sandbox user cannot). Without RUNNER_SOCKET_DIR it listens on TCP :8080.
"""

import json
import os
import signal
import socket
import socketserver
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from execute import execute

_lock = threading.Lock()
_versions: dict | None = None


def versions() -> dict:
    global _versions
    if _versions is None:

        def first(cmd):
            try:
                p = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                return (p.stdout or p.stderr).strip().splitlines()[0]
            except (OSError, subprocess.TimeoutExpired, IndexError):
                return "unavailable"

        _versions = {
            "python": first(["python3", "--version"]),
            "java": first(["java", "-version"]),
            "cpp": first(["clang++", "--version"]),
            "kotlin": first(["kotlinc", "-version"]),
        }
    return _versions


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, obj) -> None:
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            self._send(200, {"ok": True, "versions": versions()})
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/execute":
            return self._send(404, {"error": "not found"})
        try:
            req = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
            with _lock:
                self._send(200, execute(req))
        except (ValueError, KeyError) as e:
            self._send(400, {"error": str(e)})
        except Exception as e:  # keep the service alive whatever a request does
            self._send(500, {"error": f"{type(e).__name__}: {e}"})

    def log_message(self, fmt, *args):
        pass


def make_server(port: int) -> ThreadingHTTPServer:
    return ThreadingHTTPServer(("0.0.0.0", port), Handler)


class UnixHTTPServer(socketserver.ThreadingUnixStreamServer):
    daemon_threads = True


def make_unix_server(path: Path, gid: int) -> UnixHTTPServer:
    """Serve on a Unix socket readable and writable only by root and group `gid` (mode 0660)."""
    path.unlink(missing_ok=True)
    old_umask = os.umask(0o177)  # never expose the socket, even briefly, before chmod
    try:
        httpd = UnixHTTPServer(str(path), Handler)
    finally:
        os.umask(old_umask)
    os.chown(path, 0, gid)
    os.chmod(path, 0o660)
    return httpd


def main() -> None:
    socket_dir = os.environ.get("RUNNER_SOCKET_DIR")
    if not socket_dir:
        print("runner listening on :8080", flush=True)
        make_server(8080).serve_forever()
        return
    path = Path(socket_dir) / f"runner-{socket.gethostname()}.sock"
    httpd = make_unix_server(path, int(os.environ.get("RUNNER_SOCKET_GID", "1000")))

    def stop(*_: object) -> None:
        path.unlink(missing_ok=True)  # don't leave a stale socket for the app to try
        sys.exit(0)

    signal.signal(signal.SIGTERM, stop)
    print(f"runner listening on {path}", flush=True)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
