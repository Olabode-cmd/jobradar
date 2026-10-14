"""FastAPI application factory."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI

from .. import __version__
from ..config.env_file import ensure_env_file
from .dashboard import mount_dashboard
from .errors import register_error_handlers
from .routes import companies, config, export, health, jobs, runs, settings, sources
from .security import LocalOnlyMiddleware


@asynccontextmanager
async def _lifespan(_: FastAPI) -> AsyncIterator[None]:
    ensure_env_file()  # Settings writes to .env, so it must exist whenever the server is up
    yield


def create_app(dashboard_dir: Path | None = None) -> FastAPI:
    app = FastAPI(title="JobRadar", version=__version__, lifespan=_lifespan)
    app.add_middleware(LocalOnlyMiddleware)
    register_error_handlers(app)
    for module in (health, config, jobs, runs, sources, companies, settings, export):
        app.include_router(module.router)
    mount_dashboard(app, dashboard_dir)  # last, so it never shadows an API route
    return app
