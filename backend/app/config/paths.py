"""Locations of the user's files. All live at the repository root."""

from __future__ import annotations

from pathlib import Path

# backend/app/config/paths.py -> repo root
REPO_ROOT = Path(__file__).resolve().parents[3]

CONFIG_PATH = REPO_ROOT / "jobradar.config.json"
CONFIG_EXAMPLE_PATH = REPO_ROOT / "jobradar.config.example.json"
ENV_PATH = REPO_ROOT / ".env"
ENV_EXAMPLE_PATH = REPO_ROOT / ".env.example"
