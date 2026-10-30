"""HTTP front for execute(): POST /execute, GET /health. One execution at a time."""
import json
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

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
        _versions = {"python": first(["python3", "--version"]), "java": first(["java", "-version"]),
                     "cpp": first(["g++", "--version"]), "kotlin": first(["kotlinc", "-version"])}
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

    def log_message(self, fmt, *args):
        pass


def make_server(port: int) -> ThreadingHTTPServer:
    return ThreadingHTTPServer(("0.0.0.0", port), Handler)


if __name__ == "__main__":
    print("runner listening on :8080", flush=True)
    make_server(8080).serve_forever()
