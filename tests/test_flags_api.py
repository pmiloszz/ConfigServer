# tests/test_flags_api.py
import os
import tempfile
from sqlmodel import SQLModel, create_engine, Session
from fastapi.testclient import TestClient
import pytest

from main import create_app
import app.db as db_module
from app import models as models_module

@pytest.fixture
def temp_engine_and_override(monkeypatch):
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    url = f"sqlite:///{path}"
    engine = create_engine(url, connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)

    def get_session_override():
        with Session(engine) as s:
            yield s

    monkeypatch.setattr(db_module, "engine", engine)
    monkeypatch.setattr(db_module, "get_session", get_session_override)
    yield engine, path

    try:
        os.remove(path)
    except OSError:
        pass

@pytest.fixture
def client(temp_engine_and_override):
    app = create_app()
    return TestClient(app)

def test_crud_flow(client):
    payload = {"app": "demo", "env": "dev", "key": "t_feature", "value": True, "description": "init"}
    r = client.post("/flags", json=payload)
    assert r.status_code == 201
    created = r.json()
    fid = created["id"]
    version = created["version"]

    r = client.get(f"/flags/{fid}")
    assert r.status_code == 200
    assert r.json()["id"] == fid

    r = client.get("/flags", params={"app_name": "demo", "env": "dev"})
    assert r.status_code == 200
    arr = r.json()
    assert any(item["id"] == fid for item in arr)

    update_payload = {"value": False, "description": "turned off", "version": version}
    r = client.put(f"/flags/{fid}", json=update_payload)
    assert r.status_code == 200
    updated = r.json()
    assert updated["value"] is False
    assert updated["version"] == version + 1

    stale_payload = {"value": True, "description": "stale", "version": version}
    r = client.put(f"/flags/{fid}", json=stale_payload)
    assert r.status_code == 409

    r = client.delete(f"/flags/{fid}")
    assert r.status_code == 204

    r = client.get(f"/flags/{fid}")
    assert r.status_code == 404