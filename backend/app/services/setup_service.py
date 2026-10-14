"""First-run setup: create the files and database a fresh clone needs. Safe to repeat."""

from __future__ import annotations

import shutil

from ..config import paths
from ..config.env_file import ensure_env_file
from ..db import default_db_path, open_db


def run_setup() -> list[str]:
    """Create anything missing and return a line for each thing created."""
    created: list[str] = []

    if ensure_env_file():
        created.append(f"created {paths.ENV_PATH.name} (add an API_KEY there, or in the dashboard Settings, to enable the LLM pass)")

    if not paths.CONFIG_PATH.exists() and paths.CONFIG_EXAMPLE_PATH.exists():
        shutil.copyfile(paths.CONFIG_EXAMPLE_PATH, paths.CONFIG_PATH)
        created.append(f"created {paths.CONFIG_PATH.name} from the example (edit it in the dashboard Profile page)")

    db_path = default_db_path()
    existed = db_path.exists()
    open_db().close()
    if not existed:
        created.append(f"created database at {db_path}")

    return created
