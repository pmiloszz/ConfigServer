# tests/test_auth.py
#
# These tests patch settings.api_key to simulate an auth-enabled deployment.
# All other test files leave api_key="" (disabled), so they don't need changes.

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

import app.db as db_module
from app import auth as auth_module
from main import create_app

_TEST_KEY = "test-secret-key-abc123"


@pytest.fixture
def authed_client(temp_engine, monkeypatch):
    """TestClient with auth ENABLED — all requests must carry the key."""
    monkeypatch.setattr(auth_module.settings, "api_key", _TEST_KEY)

    def get_session_override():
        with Session(temp_engine) as s:
            yield s

    monkeypatch.setattr(db_module, "engine", temp_engine)
    monkeypatch.setattr(db_module, "get_session", get_session_override)

    return TestClient(create_app())


def test_request_without_key_returns_401(authed_client):
    r = authed_client.get("/flags", params={"app_name": "x", "env": "dev"})
    assert r.status_code == 401


def test_request_with_wrong_key_returns_401(authed_client):
    r = authed_client.get(
        "/flags",
        params={"app_name": "x", "env": "dev"},
        headers={"X-API-Key": "wrong-key"},
    )
    assert r.status_code == 401
    assert "Invalid" in r.json()["detail"]


def test_request_with_correct_key_succeeds(authed_client):
    r = authed_client.get(
        "/flags",
        params={"app_name": "x", "env": "dev"},
        headers={"X-API-Key": _TEST_KEY},
    )
    assert r.status_code == 200


def test_healthz_always_public(authed_client):
    """Health endpoint must work without a key — Docker/K8s probes need it."""
    r = authed_client.get("/healthz")
    assert r.status_code == 200


def test_discovery_endpoints_protected(authed_client):
    r = authed_client.get("/apps")
    assert r.status_code == 401

    r = authed_client.get("/apps", headers={"X-API-Key": _TEST_KEY})
    assert r.status_code == 200


def test_auth_disabled_when_key_not_set(client):
    """The default 'client' fixture has api_key="" — all requests pass through."""
    r = client.get("/flags", params={"app_name": "x", "env": "dev"})
    assert r.status_code == 200  # no key required, no header sent
