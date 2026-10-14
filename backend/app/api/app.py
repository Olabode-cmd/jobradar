"""FastAPI application factory."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from .. import __version__
from ..config.env_file import ensure_env_file
from .errors import register_error_handlers
from .routes import companies, config, health, jobs, runs, settings, sources
from .security import LocalOnlyMiddleware


@asynccontextmanager
async def _lifespan(_: FastAPI) -> AsyncIterator[None]:
    ensure_env_file()  # Settings writes to .env, so it must exist whenever the server is up
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="JobRadar", version=__version__, lifespan=_lifespan)
    app.add_middleware(LocalOnlyMiddleware)
    register_error_handlers(app)
    for module in (health, config, jobs, runs, sources, companies, settings):
        app.include_router(module.router)
    return app
