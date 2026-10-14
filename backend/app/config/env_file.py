"""The gitignored .env file: creation, targeted updates, and masked reads.

Keys never leave this module in full: callers get a masked hint, not the secret.
"""

from __future__ import annotations

import os
import re

from dotenv import dotenv_values, load_dotenv

from ..core.errors import InvalidInputError
from . import paths

LLM_KEYS = ("API_KEY", "LLM_PROVIDER", "LLM_MODEL", "LLM_BASE_URL")
_KEY_LINE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=")
_SAFE_VALUE = re.compile(r"^[^\s#'\"\\]*$")
_MAX_VALUE_LENGTH = 500

DEFAULT_TEMPLATE = """# JobRadar secrets. This file is gitignored: never commit it.
# One optional key powers the LLM pass. Keys starting with sk-ant- are treated as Anthropic,
# anything else as OpenAI-compatible (OpenRouter, Groq, Ollama and others).
API_KEY=

# Optional overrides
LLM_PROVIDER=
LLM_MODEL=
LLM_BASE_URL=
"""


def ensure_env_file() -> bool:
    """Create .env from .env.example (or a built-in template) if missing. Returns True if created."""
    if paths.ENV_PATH.exists():
        return False
    example = paths.ENV_EXAMPLE_PATH
    template = example.read_text(encoding="utf-8") if example.exists() else DEFAULT_TEMPLATE
    paths.ENV_PATH.write_text(template, encoding="utf-8")
    return True


def read_env_values() -> dict[str, str]:
    if not paths.ENV_PATH.exists():
        return {}
    return {key: value for key, value in dotenv_values(paths.ENV_PATH).items() if value}


def mask_secret(secret: str) -> str:
    if len(secret) <= 8:
        return "•" * len(secret)
    return f"{secret[:4]}…{secret[-4:]}"


def _validate(key: str, value: str) -> None:
    if len(value) > _MAX_VALUE_LENGTH:
        raise InvalidInputError(f"{key} is too long")
    if not _SAFE_VALUE.match(value):
        raise InvalidInputError(f"{key} cannot contain spaces, quotes, backslashes or '#'")


def update_env_values(updates: dict[str, str | None]) -> None:
    """Set or clear keys in place, keeping every other line and comment untouched.

    A value of None or "" clears the key (the line stays, empty, so the file keeps its shape).
    """
    for key, value in updates.items():
        if value:
            _validate(key, value)

    ensure_env_file()
    lines = paths.ENV_PATH.read_text(encoding="utf-8").splitlines()
    pending = dict(updates)
    for index, line in enumerate(lines):
        match = _KEY_LINE.match(line)
        if match and match.group(1) in pending:
            key = match.group(1)
            lines[index] = f"{key}={pending.pop(key) or ''}"
    lines.extend(f"{key}={value or ''}" for key, value in pending.items())

    tmp_path = paths.ENV_PATH.with_suffix(".tmp")
    tmp_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.replace(tmp_path, paths.ENV_PATH)

    for key, value in updates.items():
        if value:
            os.environ[key] = value
        else:
            os.environ.pop(key, None)
    load_dotenv(paths.ENV_PATH, override=True)
