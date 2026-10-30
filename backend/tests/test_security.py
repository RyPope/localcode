"""Browser-facing protections: DNS rebinding (Host), cross-site requests (Origin), response headers."""

import pytest
from fastapi.testclient import TestClient

from localcode.api.app import create_app
from localcode.importer import manager


@pytest.fixture
def client(data_dir, monkeypatch):
    monkeypatch.setattr(manager, "start", lambda: True)
    with TestClient(create_app(), base_url="http://localhost:4173") as c:
        yield c


@pytest.mark.parametrize("host", ["localhost:4173", "127.0.0.1:4173", "[::1]:4173", "localhost"])
def test_local_hosts_are_allowed(client, host):
    assert client.get("/api/tags", headers={"Host": host}).status_code == 200


@pytest.mark.parametrize("host", ["evil.example", "evil.example:4173", "localhost.evil.example"])
def test_foreign_host_headers_are_rejected(client, host):
    # A DNS-rebinding page reaches 127.0.0.1 under its own domain name.
    assert client.get("/api/export", headers={"Host": host}).status_code == 400


def test_cross_site_writes_are_rejected(client):
    r = client.post("/api/import", headers={"Origin": "https://evil.example"})
    assert r.status_code == 403
    r = client.put("/api/drafts/pair-sum/python", json={"code": "x"}, headers={"Origin": "null"})
    assert r.status_code == 403


def test_same_origin_and_non_browser_writes_are_allowed(client):
    assert (
        client.put(
            "/api/drafts/pair-sum/python", json={"code": "x"}, headers={"Origin": "http://localhost:4173"}
        ).status_code
        == 204
    )
    assert client.put("/api/drafts/pair-sum/python", json={"code": "x"}).status_code == 204


def test_security_headers(client):
    h = client.get("/api/tags").headers
    assert "default-src 'self'" in h["content-security-policy"]
    assert "frame-ancestors 'none'" in h["content-security-policy"]
    assert h["x-content-type-options"] == "nosniff"
    assert h["referrer-policy"] == "no-referrer"
    assert h["x-frame-options"] == "DENY"


def test_allowed_hosts_are_configurable(data_dir, monkeypatch):
    from localcode import config

    monkeypatch.setattr(manager, "start", lambda: True)
    monkeypatch.setattr(config, "ALLOWED_HOSTS", ["localcode.lan"])
    with TestClient(create_app(), base_url="http://localcode.lan") as c:
        assert c.get("/api/tags").status_code == 200
        assert c.get("/api/tags", headers={"Host": "localhost"}).status_code == 400
