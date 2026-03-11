# main.py
import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from starlette.staticfiles import StaticFiles

from app.settings import settings
from app.db import engine
from sqlmodel import SQLModel

# import router
from app.api import router as flags_router

log = logging.getLogger("uvicorn.error")

def create_app() -> FastAPI:
    app = FastAPI(title="ConfigServer")

    # register routers
    app.include_router(flags_router)

    # static
    project_root = Path(__file__).parent
    static_dir = project_root / "static"
    if static_dir.exists() and static_dir.is_dir():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    else:
        log.warning("Static directory not found: %s (skipping mount)", static_dir)

    @app.get("/healthz")
    def healthz():
        return JSONResponse({"status": "ok"})

    @app.on_event("startup")
    def on_startup():
        log.info("Application startup: checking optional DB initialization")
        try:
            # only auto-create in dev or when using sqlite for quick dev
            if settings.environment == "dev" or settings.database_url.startswith("sqlite"):
                SQLModel.metadata.create_all(engine)
                log.info("Database tables ensured (create_all) using %s", settings.database_url)
            else:
                log.info("Skipping create_all in non-dev environment")
        except Exception as exc:
            log.exception("Database initialization skipped due to error: %s", exc)

    return app

app = create_app()