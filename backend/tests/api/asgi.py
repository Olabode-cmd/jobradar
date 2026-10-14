"""Call an ASGI app directly (no httpx needed) and get back (status, headers, body)."""

from __future__ import annotations

import asyncio
from typing import Any


def request(
    app: Any, method: str, path: str, *, host: str = "localhost:8000", origin: str | None = None
) -> tuple[int, dict[str, str], bytes]:
    headers = [(b"host", host.encode())]
    if origin is not None:
        headers.append((b"origin", origin.encode()))
    scope = {
        "type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1", "method": method, "path": path,
        "raw_path": path.encode(), "query_string": b"", "headers": headers, "scheme": "http",
        "server": ("127.0.0.1", 8000), "client": ("127.0.0.1", 50000),
    }
    status: list[int] = []
    response_headers: dict[str, str] = {}
    chunks: list[bytes] = []

    delivered = False

    async def receive() -> dict[str, Any]:
        nonlocal delivered
        if not delivered:
            delivered = True
            return {"type": "http.request", "body": b"", "more_body": False}
        await asyncio.Event().wait()  # a connected client stays silent until the response is done
        return {"type": "http.disconnect"}

    async def send(message: dict[str, Any]) -> None:
        if message["type"] == "http.response.start":
            status.append(message["status"])
            response_headers.update({k.decode().lower(): v.decode() for k, v in message["headers"]})
        elif message["type"] == "http.response.body":
            chunks.append(message.get("body", b""))

    asyncio.run(app(scope, receive, send))
    return status[0], response_headers, b"".join(chunks)
