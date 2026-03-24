# main.py
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlmodel import SQLModel
from starlette.staticfiles import StaticFiles

from app.api.apps import router as apps_router
from app.api.flags import router as flags_router
from app.db import engine
from app.settings import settings

log = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    log.info("Application startup: checking optional DB initialization")
    try:
        if not getattr(settings, "use_alembic", False):
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

    log.info("Application shutdown complete")


def create_app() -> FastAPI:
    application = FastAPI(title="ConfigServer", lifespan=lifespan)

    application.include_router(flags_router)
    application.include_router(apps_router)

    project_root = Path(__file__).parent
    static_dir = project_root / "static"
    if static_dir.exists() and static_dir.is_dir():
        application.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    else:
        log.warning("Static directory not found: %s (skipping mount)", static_dir)

    @application.get("/healthz")
    def healthz():
        return JSONResponse({"status": "ok"})

    return application


app = create_app()
