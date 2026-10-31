"""Client for the runner service (see runner/server.py).

In Docker the runner has no network at all; each replica serves HTTP on a Unix socket named
`runner-<host>.sock` in a shared directory, configured as `LOCALCODE_RUNNER=unix:<directory>`.
For development and tests, `LOCALCODE_RUNNER` can also be a plain `http://host:port` URL.
"""

import random
from pathlib import Path

import httpx

from localcode import config
from localcode.judging.types import RunnerRequest, RunnerResult

# Compile time plus process start-up on top of the run's own limit.
_OVERHEAD_S = 90
_UNIX = "unix:"
_versions: dict[str, str] | None = None


class RunnerUnavailable(Exception):
    """The runner could not be reached or rejected the request."""


def endpoints() -> list[str]:
    """Every runner the app can use: one per socket in the socket directory, or the configured URL."""
    target = config.RUNNER_URL
    if target.startswith(_UNIX):
        return sorted(f"{_UNIX}{p}" for p in Path(target.removeprefix(_UNIX)).glob("runner-*.sock"))
    return [target]


def _client(endpoint: str, timeout: float) -> httpx.Client:
    if endpoint.startswith(_UNIX):
        transport = httpx.HTTPTransport(uds=endpoint.removeprefix(_UNIX))
        return httpx.Client(transport=transport, base_url="http://runner", timeout=timeout)
    return httpx.Client(base_url=endpoint, timeout=timeout)


def execute(req: RunnerRequest, endpoint: str | None = None) -> RunnerResult:
    """Run a submission on `endpoint`, or on any available runner (stale sockets are skipped)."""
    candidates = [endpoint] if endpoint else random.sample(endpoints(), k=len(endpoints()))
    if not candidates:
        raise RunnerUnavailable(f"no runner found at {config.RUNNER_URL}")
    timeout = req["timeout_ms"] / 1000 + _OVERHEAD_S
    errors = []
    for candidate in candidates:
        try:
            with _client(candidate, timeout) as client:
                r = client.post("/execute", json=req)
        except httpx.ConnectError as e:  # nothing was sent, so another runner may take it
            errors.append(f"{candidate}: {e}")
            continue
        except httpx.HTTPError as e:
            raise RunnerUnavailable(f"{type(e).__name__}: {e}") from e
        if r.status_code != 200:
            try:
                detail = r.json().get("error", r.text)
            except ValueError:
                detail = r.text
            raise RunnerUnavailable(f"HTTP {r.status_code}: {detail}")
        return r.json()
    raise RunnerUnavailable("; ".join(errors))


def versions() -> dict[str, str] | None:
    """Toolchain versions reported by the runner (cached once available)."""
    global _versions
    if _versions is None:
        for endpoint in endpoints():
            try:
                with _client(endpoint, 60) as client:
                    _versions = client.get("/health").json()["versions"]
                    break
            except httpx.HTTPError, KeyError, ValueError:
                continue
    return _versions
