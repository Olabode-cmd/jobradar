"""JobRadar API. Phase 0: /api/health only; routes land with the dashboard."""

from __future__ import annotations

from fastapi import FastAPI

from .config import llm_settings, load_config
from .config_routes import router as config_router
from .db import open_db
from .security import LocalOnlyMiddleware

app = FastAPI(title="JobRadar", version="0.1.0")
app.add_middleware(LocalOnlyMiddleware)
app.include_router(config_router)


@app.get("/api/health")
def health() -> dict:
    cfg = load_config()
    conn = open_db()
    try:
        conn.execute("SELECT 1 FROM meta LIMIT 1")
        db = "ok"
    except Exception as exc:  # surface any DB failure in the health report
        db = f"error: {exc}"
    finally:
        conn.close()

    return {
        "status": "ok",
        "db": db,
        "config_loaded": cfg.present,
        "profile_role": cfg.profile_role,
        "config_errors": cfg.errors,
        "llm": llm_settings()["enabled"],
    }