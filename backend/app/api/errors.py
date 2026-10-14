"""Map application errors to HTTP responses."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from ..core.errors import ConflictError, InvalidInputError, NotFoundError

_STATUS_BY_ERROR = ((NotFoundError, 404), (ConflictError, 409), (InvalidInputError, 422))


def register_error_handlers(app: FastAPI) -> None:
    for error_type, status in _STATUS_BY_ERROR:

        async def handler(_: Request, exc: Exception, status: int = status) -> JSONResponse:
            return JSONResponse({"detail": str(exc)}, status_code=status)

        app.add_exception_handler(error_type, handler)
