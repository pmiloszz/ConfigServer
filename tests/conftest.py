# tests/conftest.py
#
# HOW DATABASE SELECTION WORKS:
#   - No DATABASE_URL env var (or SQLite URL) → uses a temp .db file, deleted after each test.
#     This is the default for local development — no Docker needed.
#   - DATABASE_URL starts with "postgresql" → uses that PostgreSQL instance directly.
#     Tables are created before each test and dropped afterward for full isolation.
#     This is what CI uses (the GitHub Actions service container).
#
# Either way, every test gets a clean, empty database. The tests themselves
# never need to know or care which backend is running.

import os
import tempfile
from contextlib import suppress

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

import app.db as db_module
from app.repositories.flag_repository import FlagRepository
from app.services.flag_service import FlagService
from main import create_app


def _make_engine():
    """
    Return a SQLAlchemy engine pointed at the right database.

    The function checks DATABASE_URL at call time so that
    pytest-xdist workers (if ever used) each get their own engine.
    """
    db_url = os.environ.get("DATABASE_URL", "")

    if db_url.startswith("postgresql"):
        # CI path: connect to the running PostgreSQL service container.
        # psycopg3 is the driver (postgresql+psycopg://...).
        return create_engine(db_url), None  # (engine, tmp_path)

    # Local path: create a real temporary file (not :memory:) so that
    # the same engine can be shared across threads in the TestClient.
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    engine = create_engine(
        f"sqlite:///{path}",
        connect_args={"check_same_thread": False},
    )
    return engine, path


@pytest.fixture
def temp_engine():
    engine, tmp_path = _make_engine()
    SQLModel.metadata.create_all(engine)

    yield engine

    # Teardown: wipe everything so the next test starts clean.
    SQLModel.metadata.drop_all(engine)
    engine.dispose()

    if tmp_path:
        with suppress(OSError):
            os.remove(tmp_path)


@pytest.fixture
def session(temp_engine):
    with Session(temp_engine) as s:
        yield s


@pytest.fixture
def flag_repository(session):
    return FlagRepository(session)


@pytest.fixture
def flag_service(flag_repository):
    return FlagService(flag_repository)


@pytest.fixture
def client(temp_engine, monkeypatch):
    def get_session_override():
        with Session(temp_engine) as s:
            yield s

    monkeypatch.setattr(db_module, "engine", temp_engine)
    monkeypatch.setattr(db_module, "get_session", get_session_override)

    application = create_app()
    return TestClient(application)
