"""Protections for an unauthenticated app listening on localhost.

- Host allow-list: defeats DNS rebinding, where a web page re-points its own domain at 127.0.0.1
  to make the browser treat localcode as same-origin.
- Origin check on state-changing requests: blocks cross-site requests from other pages (CSRF).
  Requests without an Origin header (curl, scripts) are allowed; they aren't sent by browsers
  for cross-site writes.
- Security headers, including a content security policy that limits the impact of any HTML
  that slips past sanitisation.
"""

from collections.abc import Awaitable, Callable
from urllib.parse import urlsplit

from fastapi import FastAPI, Request, Response
from fastapi.responses import PlainTextResponse

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}

CONTENT_SECURITY_POLICY = "; ".join(
    [
        "default-src 'self'",
        "script-src 'self'",
        "style-src 'self' 'unsafe-inline'",  # React style props, Monaco and KaTeX inject styles
        "img-src 'self' data: https:",  # some problem statements embed images from public CDNs
        "font-src 'self' data:",
        "connect-src 'self'",
        "worker-src 'self' blob:",
        "object-src 'none'",
        "base-uri 'self'",
        "form-action 'self'",
        "frame-ancestors 'none'",
    ]
)
HEADERS = {
    "Content-Security-Policy": CONTENT_SECURITY_POLICY,
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Cross-Origin-Opener-Policy": "same-origin",
}


def _hostname(netloc: str) -> str:
    """Host without port: 'localhost:4173' -> 'localhost', '[::1]:4173' -> '::1'."""
    return urlsplit(f"//{netloc}").hostname or ""


def _is_cross_site(origin: str, allowed: set[str]) -> bool:
    return origin == "null" or _hostname(urlsplit(origin).netloc).lower() not in allowed


def install(app: FastAPI, allowed_hosts: list[str]) -> None:
    allowed = {h.lower() for h in allowed_hosts}

    @app.middleware("http")
    async def protect(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        if _hostname(request.headers.get("host", "")).lower() not in allowed:
            return PlainTextResponse("Invalid host header", status_code=400)
        origin = request.headers.get("origin")
        if request.method not in SAFE_METHODS and origin is not None and _is_cross_site(origin, allowed):
            return PlainTextResponse("Cross-site request blocked", status_code=403)
        response = await call_next(request)
        response.headers.update(HEADERS)
        return response
