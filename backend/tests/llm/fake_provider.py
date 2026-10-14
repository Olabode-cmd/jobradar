"""A local HTTP server that imitates an LLM provider and records the requests it receives."""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any


class FakeProvider:
    """Serves one canned (status, body) per request path and keeps every request for assertions."""

    def __init__(self, routes: dict[str, tuple[int, Any]]) -> None:
        self.routes = routes
        self.requests: list[dict[str, Any]] = []
        provider = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:  # noqa: N802
                length = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(length) or b"{}")
                provider.requests.append({"path": self.path, "headers": dict(self.headers), "body": body})
                status, payload = provider.routes.get(self.path, (404, {"error": {"message": "no such route"}}))
                data = json.dumps(payload).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def log_message(self, *_: Any) -> None:
                pass

        self._server = HTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self._server.server_port}"
        threading.Thread(target=self._server.serve_forever, daemon=True).start()

    def close(self) -> None:
        self._server.shutdown()
        self._server.server_close()
