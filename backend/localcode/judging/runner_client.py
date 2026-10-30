"""HTTP client for the runner service (see runner/server.py)."""

import httpx

from localcode import config
from localcode.judging.types import RunnerRequest, RunnerResult

# Compile time plus process start-up on top of the run's own limit.
_OVERHEAD_S = 90
_versions: dict[str, str] | None = None


class RunnerUnavailable(Exception):
    """The runner could not be reached or rejected the request."""


def execute(req: RunnerRequest, base_url: str | None = None) -> RunnerResult:
    url = base_url or config.RUNNER_URL
    try:
        r = httpx.post(f"{url}/execute", json=req, timeout=req["timeout_ms"] / 1000 + _OVERHEAD_S)
    except httpx.HTTPError as e:
        raise RunnerUnavailable(f"{type(e).__name__}: {e}") from e
    if r.status_code != 200:
        try:
            detail = r.json().get("error", r.text)
        except ValueError:
            detail = r.text
        raise RunnerUnavailable(f"HTTP {r.status_code}: {detail}")
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
