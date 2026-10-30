"""HTTP client for the runner service."""
import httpx

from localcode import config

_versions: dict | None = None


def execute(req: dict) -> dict:
    timeout = req.get("timeout_ms", 10000) / 1000 + 90  # compile time + startup on top of the run limit
    r = httpx.post(f"{config.RUNNER_URL}/execute", json=req, timeout=timeout)
    r.raise_for_status()
    return r.json()


def versions() -> dict | None:
    global _versions
    if _versions is None:
        try:
            _versions = httpx.get(f"{config.RUNNER_URL}/health", timeout=60).json()["versions"]
        except (httpx.HTTPError, KeyError, ValueError):
            return None
    return _versions
