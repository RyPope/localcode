from fastapi.testclient import TestClient

from localcode import config
from localcode.api.app import create_app
from localcode.api.deps import get_runner


def client(runner):
    app = create_app()
    app.dependency_overrides[get_runner] = lambda: runner
    return TestClient(app)


def test_problems_endpoint(data_dir, runner):
    r = client(runner).get("/api/problems", params={"company": "acme", "window": "all"})
    assert r.status_code == 200
    assert [p["slug"] for p in r.json()["items"]] == ["pair-sum", "tree-mirror"]


def test_unknown_problem_is_404(data_dir, runner):
    assert client(runner).get("/api/problems/nope").status_code == 404


def test_run_rejects_bad_custom_input(data_dir, runner):
    r = client(runner).post(
        "/api/run", json={"slug": "pair-sum", "lang": "python", "code": "x", "custom": ["nums = [1"]}
    )
    assert r.status_code == 400
    assert "Custom case 1" in r.json()["detail"]


def test_draft_put_get(data_dir, runner):
    c = client(runner)
    assert c.put("/api/drafts/pair-sum/java", json={"code": "abc"}).status_code == 204
    assert c.get("/api/drafts/pair-sum/java").json() == {"code": "abc"}
    assert c.get("/api/drafts/pair-sum/cpp").json() == {"code": None}


def test_status_reports_imported(data_dir, runner):
    s = client(runner).get("/api/status").json()
    assert s["imported"] is True
    assert s["import"]["running"] is False
    assert s["meta"]["stats"]["problems"] == 4


def test_spa_fallback_serves_index(data_dir, runner, tmp_path, monkeypatch):
    dist = tmp_path / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text("<html>app</html>")
    (dist / "assets" / "a.js").write_text("js")
    monkeypatch.setattr(config, "WEB_DIST", dist)
    c = client(runner)
    assert c.get("/problems/two-sum").text == "<html>app</html>"
    assert c.get("/assets/a.js").text == "js"
    assert c.get("/api/nope").status_code == 404


def test_unknown_language_is_422(data_dir, runner):
    r = client(runner).post("/api/submit", json={"slug": "pair-sum", "lang": "ruby", "code": "x"})
    assert r.status_code == 422


def test_run_rejects_set_literal_with_400(data_dir, runner):
    r = client(runner).post(
        "/api/run", json={"slug": "pair-sum", "lang": "python", "code": "x", "custom": ["nums = {1, 2}, goal = 3"]}
    )
    assert r.status_code == 400
    assert "must be a number" in r.json()["detail"]


def test_problems_before_import_is_503_and_status_not_imported(tmp_path, monkeypatch, runner):
    from localcode import db
    from localcode.importer import manager

    monkeypatch.setattr(db, "CONTENT_DB", tmp_path / "content.db")
    monkeypatch.setattr(db, "USER_DB", tmp_path / "user.db")
    monkeypatch.setattr(manager, "start", lambda: True)  # no real import from the lifespan hook
    with client(runner) as c:
        assert c.get("/api/problems").status_code == 503
        assert c.get("/api/status").json()["imported"] is False
