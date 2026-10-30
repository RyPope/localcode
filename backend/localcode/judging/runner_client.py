"""HTTP client for the runner service (see runner/server.py)."""

import httpx

from localcode import config
from localcode.judging.types import RunnerRequest, RunnerResult

# Compile time plus process start-up on top of the run's own limit.
_OVERHEAD_S = 90
_versions: dict[str, str] | None = None


def execute(req: RunnerRequest, base_url: str | None = None) -> RunnerResult:
    url = base_url or config.RUNNER_URL
    r = httpx.post(f"{url}/execute", json=req, timeout=req["timeout_ms"] / 1000 + _OVERHEAD_S)
    r.raise_for_status()
    return r.json()


def versions() -> dict[str, str] | None:
    """Toolchain versions reported by the runner (cached once available)."""
    global _versions
    if _versions is None:
        try:
            _versions = httpx.get(f"{config.RUNNER_URL}/health", timeout=60).json()["versions"]
        except (httpx.HTTPError, KeyError, ValueError):
            return None
    return _versions
