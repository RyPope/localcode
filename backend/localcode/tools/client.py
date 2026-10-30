"""Minimal HTTP client for maintainer tools that drive a running localcode instance."""

from typing import Any

import httpx

DEFAULT_BASE_URL = "http://localhost:4173"


class LocalcodeClient:
    def __init__(self, base_url: str = DEFAULT_BASE_URL, timeout: float = 300) -> None:
        self._http = httpx.Client(base_url=base_url, timeout=timeout)

    def get(self, path: str, **params: Any) -> Any:
        return self._http.get(path, params=params or None).raise_for_status().json()

    def post(self, path: str, body: dict) -> tuple[int, Any]:
        """Returns (status, json) without raising, so callers can assert on error responses too."""
        r = self._http.post(path, json=body)
        return r.status_code, r.json()

    def submit(self, slug: str, lang: str, code: str) -> tuple[int, Any]:
        return self.post("/api/submit", {"slug": slug, "lang": lang, "code": code})
