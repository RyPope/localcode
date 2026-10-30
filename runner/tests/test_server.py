import http.client
import os
import socket
import stat
import tempfile
import threading
from pathlib import Path

import server

APP_GID = 4321


class UnixHTTPConnection(http.client.HTTPConnection):
    def __init__(self, path: str):
        super().__init__("runner")
        self._path = path

    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.connect(self._path)


def test_unix_socket_server_is_restricted_to_the_app_group():
    path = Path(tempfile.mkdtemp(prefix="rs-", dir="/tmp")) / "runner-test.sock"
    httpd = server.make_unix_server(path, APP_GID)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        st = path.stat()
        assert stat.S_IMODE(st.st_mode) == 0o660
        assert st.st_gid == APP_GID and st.st_uid == 0
        conn = UnixHTTPConnection(str(path))
        conn.request("GET", "/health")
        assert conn.getresponse().status == 200
    finally:
        httpd.shutdown()
        httpd.server_close()


def test_sandbox_user_cannot_connect_to_the_socket():
    path = Path(tempfile.mkdtemp(prefix="rs-", dir="/tmp")) / "runner-test.sock"
    httpd = server.make_unix_server(path, APP_GID)
    try:
        pid = os.fork()
        if pid == 0:  # child: become the sandbox user and try to connect
            os.setgroups([])
            os.setgid(10001)
            os.setuid(10001)
            try:
                socket.socket(socket.AF_UNIX).connect(str(path))
                os._exit(1)
            except PermissionError:
                os._exit(0)
        _, status = os.waitpid(pid, 0)
        assert os.waitstatus_to_exitcode(status) == 0
    finally:
        httpd.server_close()
