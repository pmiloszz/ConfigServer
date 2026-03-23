# main.py
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlmodel import SQLModel
from starlette.staticfiles import StaticFiles

# router
from app.api.flags import router as flags_router
from app.db import engine
from app.settings import settings

log = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """
    Application lifespan handler: deterministic startup and shutdown.

    - If use_alembic is True, migrations are expected to be applied externally
      (CI / deploy). In that case we skip create_all to avoid schema drift.
    - If use_alembic is False, we create tables automatically for quick dev.
    """
    log.info("Application startup: checking optional DB initialization")
    try:
        # If Alembic is enabled, do not call create_all here.
        if not getattr(settings, "use_alembic", False):
            # Only auto-create in dev or when using sqlite for quick local dev
            if settings.environment == "dev" or settings.database_url.startswith("sqlite"):
                SQLModel.metadata.create_all(engine)
                log.info("Database tables ensured (create_all) using %s", settings.database_url)
            else:
                log.info("Skipping create_all in non-dev environment")
        else:
            log.info("use_alembic is True; skipping create_all and expecting migrations to be applied")
    except Exception as exc:
        log.exception("Database initialization skipped due to error: %s", exc)

    yield

    # shutdown hook (extend if you need to close resources)
    log.info("Application shutdown complete")


def create_app() -> FastAPI:
    """Factory to create and configure the FastAPI application."""
    app = FastAPI(title="ConfigServer", lifespan=lifespan)

    # register routers
    app.include_router(flags_router)

    # static files (optional)
    project_root = Path(__file__).parent
    static_dir = project_root / "static"
    if static_dir.exists() and static_dir.is_dir():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    else:
        log.warning("Static directory not found: %s (skipping mount)", static_dir)

    @app.get("/healthz")
    def healthz():
        return JSONResponse({"status": "ok"})

    return app


# module-level app for uvicorn/uv
app = create_app()
