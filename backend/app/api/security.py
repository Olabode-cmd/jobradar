"""Localhost hardening (PRD 8.5): reject foreign Host headers and cross-origin writes."""

from __future__ import annotations

from urllib.parse import urlsplit

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

LOCAL_HOSTNAMES = frozenset({"localhost", "127.0.0.1", "::1"})
SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})


def _hostname(value: str) -> str | None:
    try:
        return urlsplit(value if "://" in value else f"//{value}").hostname
    except ValueError:
        return None


class LocalOnlyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _hostname(request.headers.get("host", "")) not in LOCAL_HOSTNAMES:
            return JSONResponse({"detail": "Host not allowed"}, status_code=403)

        origin = request.headers.get("origin")
        if request.method not in SAFE_METHODS and origin is not None and _hostname(origin) not in LOCAL_HOSTNAMES:
            return JSONResponse({"detail": "Origin not allowed"}, status_code=403)

        return await call_next(request)
