import json
import threading
import urllib.request

import pytest
import server


@pytest.fixture(scope="session")
def url():
    httpd = server.make_server(0)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()


@pytest.fixture
def run(url):
    def _run(lang, code, method, params, cases, timeout_ms=10000, cpp_sig=None, ret=None):
        body = json.dumps(
            {
                "lang": lang,
                "code": code,
                "method": method,
                "params": params,
                "cases": cases,
                "timeout_ms": timeout_ms,
                "cpp_sig": cpp_sig,
                "ret": ret,
            }
        ).encode()
        req = urllib.request.Request(url + "/execute", body, {"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.load(r)

    return _run
