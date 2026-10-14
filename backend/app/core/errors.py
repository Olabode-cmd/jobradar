"""Application errors. They carry no HTTP knowledge; the API layer maps them to responses."""

from __future__ import annotations


class AppError(Exception):
    """Base for errors a caller can act on."""


class NotFoundError(AppError):
    """The requested thing does not exist."""


class ConflictError(AppError):
    """The request is valid but clashes with current state (for example an active run)."""


class InvalidInputError(AppError):
    """The request is well-formed but its values are unacceptable."""
