# tests/test_flags_api.py


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
    assert any(item["id"] == fid for item in r.json())

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


def test_create_duplicate_returns_409(client):
    payload = {"app": "demo", "env": "dev", "key": "dup_key", "value": True, "description": "first"}
    r = client.post("/flags", json=payload)
    assert r.status_code == 201

    r = client.post("/flags", json=payload)
    assert r.status_code == 409
    assert "already exists" in r.json()["detail"].lower()


def test_update_nonexistent_returns_404(client):
    r = client.put("/flags/999999", json={"value": False, "description": "missing", "version": 1})
    assert r.status_code == 404
    assert "not found" in r.json()["detail"].lower()


def test_delete_nonexistent_returns_404(client):
    r = client.delete("/flags/999999")
    assert r.status_code == 404
    assert "not found" in r.json()["detail"].lower()


# --- limit parameter tests ---


def test_list_default_limit_returns_flags(client):
    """Default call without limit param should work fine."""
    for i in range(3):
        client.post("/flags", json={"app": "pg", "env": "dev", "key": f"f{i}", "value": True})

    r = client.get("/flags", params={"app_name": "pg", "env": "dev"})
    assert r.status_code == 200
    assert len(r.json()) == 3


def test_list_with_explicit_limit(client):
    for i in range(5):
        client.post("/flags", json={"app": "lim", "env": "dev", "key": f"flag_{i}", "value": True})

    r = client.get("/flags", params={"app_name": "lim", "env": "dev", "limit": 2})
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_list_limit_zero_rejected(client):
    """limit=0 is below the minimum of 1 — FastAPI should reject it."""
    r = client.get("/flags", params={"app_name": "x", "env": "dev", "limit": 0})
    assert r.status_code == 422


def test_list_limit_above_max_rejected(client):
    """limit=501 exceeds the hard cap of 500 — FastAPI should reject it."""
    r = client.get("/flags", params={"app_name": "x", "env": "dev", "limit": 501})
    assert r.status_code == 422
