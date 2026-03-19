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


@pytest.fixture
def temp_engine():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    url = f"sqlite:///{path}"
    engine = create_engine(url, connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)

    try:
        yield engine
    finally:
        with suppress(OSError):
            os.remove(path)


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

    app = create_app()
    return TestClient(app)
