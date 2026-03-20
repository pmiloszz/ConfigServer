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


def test_create_duplicate_returns_409(client):
    payload = {"app": "demo", "env": "dev", "key": "dup_key", "value": True, "description": "first"}
    r = client.post("/flags", json=payload)
    assert r.status_code == 201

    r = client.post("/flags", json=payload)
    assert r.status_code == 409
    assert "already exists" in r.json()["detail"].lower()


def test_update_nonexistent_returns_404(client):
    update_payload = {"value": False, "description": "missing", "version": 1}
    r = client.put("/flags/999999", json=update_payload)
    assert r.status_code == 404
    assert "not found" in r.json()["detail"].lower()


def test_delete_nonexistent_returns_404(client):
    r = client.delete("/flags/999999")
    assert r.status_code == 404
    assert "not found" in r.json()["detail"].lower()
