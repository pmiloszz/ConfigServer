# main.py
import os
import logging

from pathlib import Path
from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse
from starlette.staticfiles import StaticFiles

# optional DB imports
from sqlmodel import SQLModel, select
from app.db import engine, get_session
from app.models import Flag

log = logging.getLogger("uvicorn.error")
app = FastAPI(title="ConfigServer")  # app has to be defined before imports that use it (e.g. for router) to avoid circular imports

# import for router
from app.api import router as flags_router

# router
app.include_router(flags_router)

# --- static (mount only if directory exists) ---
project_root = Path(__file__).parent
static_dir = project_root / "static"
if static_dir.exists() and static_dir.is_dir():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
else:
    log.warning("Static directory not found: %s (skipping mount)", static_dir)

# --- health endpoint ---
@app.get("/healthz")
def healthz():
    return JSONResponse({"status": "ok"})

# --- startup: DB init and other (startup function) ---
DATABASE_URL = os.getenv("DATABASE_URL")

@app.on_event("startup")
def app_startup():
    log.info("Application startup: checking optional DB initialization")
    # init only if we have DATABASE_URL i SQLModel
    try:
        if DATABASE_URL:
            # create_engine import in app.db; use engine from app.db just in dev fallback
            SQLModel.metadata.create_all(engine)  # dev only; in production use Alembic
            log.info("Database tables ensured (create_all) using %s", DATABASE_URL)
        else:
            log.info("No DATABASE_URL provided; skipping DB init")
    except Exception as exc:
        log.exception("Database initialization skipped due to error: %s", exc)

# --- example endpoint CRUD (sync) ---
@app.get("/flags")
def list_flags(app_name: str, env: str, session = Depends(get_session)):
    stmt = select(Flag).where(Flag.app == app_name, Flag.env == env)
    return session.exec(stmt).all()

# --- root ---
@app.get("/")
def root():
    return {"message": "ConfigServer running"}