"""Serve the built dashboard (web/dist) from the API, with a fallback to index.html for client-side routes."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from ..config.paths import REPO_ROOT

DEFAULT_DASHBOARD_DIR = REPO_ROOT / "web" / "dist"


def mount_dashboard(app: FastAPI, directory: Path | None = None) -> bool:
    """Register the catch-all route if a build exists. Returns whether it was mounted."""
    root = (directory or DEFAULT_DASHBOARD_DIR).resolve()
    index = root / "index.html"
    if not index.is_file():
        return False

    @app.get("/{path:path}", include_in_schema=False)
    def serve_dashboard(path: str) -> FileResponse:
        if path == "api" or path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found")
        candidate = (root / path).resolve()
        # resolve() collapses "..", so this rejects anything that escapes the build directory
        if candidate.is_file() and candidate.is_relative_to(root):
            return FileResponse(candidate)
        return FileResponse(index)

    return True
