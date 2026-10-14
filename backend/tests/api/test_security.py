"""Host/Origin guard, driven through a bare ASGI call."""

import asyncio
import unittest

from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route

from app.api.security import LocalOnlyMiddleware


async def _ok(request):
    return PlainTextResponse("ok")


APP = Starlette(routes=[Route("/", _ok, methods=["GET", "PUT"])])
APP.add_middleware(LocalOnlyMiddleware)


def call(method: str, host: str, origin: str | None = None) -> int:
    headers = [(b"host", host.encode())]
    if origin is not None:
        headers.append((b"origin", origin.encode()))
    scope = {
        "type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1", "method": method, "path": "/",
        "raw_path": b"/", "query_string": b"", "headers": headers, "scheme": "http",
        "server": ("127.0.0.1", 8000), "client": ("127.0.0.1", 50000),
    }
    status: list[int] = []

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        if message["type"] == "http.response.start":
            status.append(message["status"])

    asyncio.run(APP(scope, receive, send))
    return status[0]


class LocalOnlyTests(unittest.TestCase):
    def test_local_hosts_pass(self):
        for host in ["localhost:8000", "127.0.0.1:8000", "[::1]:8000", "localhost"]:
            with self.subTest(host=host):
                self.assertEqual(call("GET", host), 200)

    def test_foreign_host_is_rejected(self):
        self.assertEqual(call("GET", "evil.example.com"), 403)

    def test_cross_origin_write_is_rejected(self):
        self.assertEqual(call("PUT", "localhost:8000", "https://evil.example.com"), 403)
        self.assertEqual(call("PUT", "localhost:8000", "null"), 403)

    def test_local_origin_write_passes(self):
        self.assertEqual(call("PUT", "localhost:8000", "http://localhost:5173"), 200)

    def test_write_without_origin_passes(self):
        self.assertEqual(call("PUT", "127.0.0.1:8000"), 200)

    def test_cross_origin_read_is_not_blocked_by_origin_check(self):
        self.assertEqual(call("GET", "localhost:8000", "https://evil.example.com"), 200)


if __name__ == "__main__":
    unittest.main()
