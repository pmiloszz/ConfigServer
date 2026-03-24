# tests/test_apps_api.py


def test_list_apps_empty(client):
    r = client.get("/apps")
    assert r.status_code == 200
    assert r.json() == []


def test_list_apps_returns_distinct_sorted(client):
    client.post("/flags", json={"app": "zebra", "env": "dev", "key": "k1", "value": True})
    client.post("/flags", json={"app": "alpha", "env": "dev", "key": "k2", "value": True})
    client.post("/flags", json={"app": "zebra", "env": "prod", "key": "k3", "value": True})

    r = client.get("/apps")
    assert r.status_code == 200
    apps = r.json()

    # distinct: "zebra" appears twice in flags but once here
    assert apps == ["alpha", "zebra"]


def test_list_envs_empty_for_unknown_app(client):
    r = client.get("/apps/nonexistent/envs")
    assert r.status_code == 200
    assert r.json() == []


def test_list_envs_returns_distinct_sorted(client):
    client.post("/flags", json={"app": "myapp", "env": "prod", "key": "k1", "value": True})
    client.post("/flags", json={"app": "myapp", "env": "dev", "key": "k2", "value": True})
    client.post("/flags", json={"app": "myapp", "env": "staging", "key": "k3", "value": True})
    # second flag in prod — should not produce duplicate "prod" in results
    client.post("/flags", json={"app": "myapp", "env": "prod", "key": "k4", "value": False})

    r = client.get("/apps/myapp/envs")
    assert r.status_code == 200
    envs = r.json()

    assert envs == ["dev", "prod", "staging"]


def test_list_envs_only_for_requested_app(client):
    client.post("/flags", json={"app": "app_a", "env": "dev", "key": "k1", "value": True})
    client.post("/flags", json={"app": "app_b", "env": "prod", "key": "k2", "value": True})

    r = client.get("/apps/app_a/envs")
    assert r.json() == ["dev"]  # app_b's "prod" must not appear
