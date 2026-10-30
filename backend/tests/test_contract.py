"""Every endpoint's real output must validate against its declared response model."""

import pytest
from fastapi.testclient import TestClient

from localcode.api.app import create_app
from localcode.api.deps import get_runner
from localcode.importer import manager

GETS = [
    "/api/status",
    "/api/problems",
    "/api/problems?company=acme&window=all&sort=frequency",
    "/api/tags",
    "/api/problems/pair-sum",
    "/api/problems/fill-in-place",
    "/api/problems/pair-sum/solutions",
    "/api/drafts/pair-sum/python",
    "/api/submissions/pair-sum",
    "/api/companies",
    "/api/companies/acme?window=30d",
    "/api/stats",
    "/api/export",
]


@pytest.fixture
def client(data_dir, runner, monkeypatch):
    monkeypatch.setattr(manager, "start", lambda: True)
    runner.user = {"compile_error": None, "timed_out": False, "memory_kb": 1, "exit_code": 0, "stderr": "",
                   "results": [{"ok": True, "value": v, "stdout": "", "ms": 1} for v in ([1, 2], [0, 1], [0, 2], [0, 1])]}
    runner.ref_values = {"[[1, 4, 6], 10]": [1, 2], "[[5, 5], 10]": [0, 1]}
    app = create_app()
    app.dependency_overrides[get_runner] = lambda: runner
    with TestClient(app) as c:
        c.put("/api/drafts/pair-sum/python", json={"code": "x"})
        assert c.post("/api/submit", json={"slug": "pair-sum", "lang": "python", "code": "x"}).status_code == 200
        yield c


@pytest.mark.parametrize("path", GETS)
def test_get_endpoints_match_their_models(client, path):
    assert client.get(path).status_code == 200


def test_run_matches_its_model(client):
    r = client.post("/api/run", json={"slug": "pair-sum", "lang": "python", "code": "x"})
    assert r.status_code == 200
    assert set(r.json()) == {"verdict", "compile_error", "cases"}


def test_invalid_window_is_rejected_by_validation(client):
    assert client.get("/api/problems?window=1y").status_code == 422
