# ConfigServer

![Python](https://img.shields.io/badge/python-3.14-3776ab?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.134-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-336791?logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-ready-2496ed?logo=docker&logoColor=white)
![Kubernetes](https://img.shields.io/badge/Kubernetes-ready-326ce5?logo=kubernetes&logoColor=white)
![Prometheus](https://img.shields.io/badge/Prometheus-monitored-e6522c?logo=prometheus&logoColor=white)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
![CI](https://github.com/pmiloszz/ConfigServer/actions/workflows/github_CI.yml/badge.svg)

**Live (dev):** [Web UI](https://configserver-dev.501404.xyz/static/index.html) · [API docs](https://configserver-dev.501404.xyz/docs)

ConfigServer is a self-hosted feature-flag and config service built with **FastAPI** and **SQLModel**. It gives every application a simple REST API to read and write boolean flags scoped by `app` + `env` + `key`, with **optimistic concurrency control** so simultaneous writers can never silently overwrite each other.

The backend runs anywhere Python runs. A fully static browser UI ships alongside it so you can manage flags without writing a single line of client code. For production, a Kustomize-based Kubernetes setup splits the API and an NGINX frontend into separate images behind an ingress, with PostgreSQL on a StatefulSet.

---

## Features

| Need | How ConfigServer covers it |
|------|---------------------------|
| Toggle features without a redeploy | REST `PUT /flags/{id}` — update `value` from anywhere |
| Multiple apps and environments in one place | Every flag is namespaced by `app` + `env` + `key` |
| Prevent split-brain on concurrent updates | `version` field: server returns `409 Conflict` if the flag changed between your read and write |
| No external config store dependency locally | SQLite by default — zero extra services needed |
| Production-grade storage | Drop-in PostgreSQL via a single env var change |
| Zero-infra management UI | Vanilla-JS dashboard at `/static/index.html` — bulk ops, rollout workflow, audit feed, themes |
| Kubernetes-ready | Kustomize base + dev/prod overlays, NGINX reverse-proxy frontend, health probes, secrets |
| GitOps delivery | Every push to `main` builds images, patches manifests, and the cluster self-reconciles — no manual deploys |
| Observability | Prometheus metrics at `/metrics` — HTTP latency, flag operations, auth failures, version conflicts |
| Optional authentication | `X-API-Key` header auth — disabled by default, one env var to enable |
| Versioned schema migrations | Alembic records every structural DB change as a reversible, reviewable file |
| Fast inner dev loop | Docker Compose dev override mounts source and hot-reloads — no rebuild on save |

## Tech stack

| Layer | Technology |
|-------|-----------|
| **Language** | Python 3.14 |
| **Web framework** | FastAPI + Starlette (static file serving) |
| **ASGI server** | Uvicorn |
| **Validation / settings** | Pydantic v2, pydantic-settings |
| **ORM** | SQLModel (SQLAlchemy 2.x) |
| **Database driver** | psycopg 3 (PostgreSQL), built-in SQLite for dev/test |
| **Migrations** | Alembic |
| **Package manager** | uv (lockfile: `uv.lock`) |
| **Build backend** | Hatchling |
| **Frontend** | Vanilla HTML / CSS / JavaScript — no framework |
| **Frontend server (K8s)** | NGINX 1.29-alpine (serves static assets, reverse-proxies API routes) |
| **Containerisation** | Docker (multi-stage build via uv), Docker Compose |
| **Orchestration** | Kubernetes + Kustomize (base + dev/prod overlays) |
| **Database (ops)** | PostgreSQL 17-alpine |
| **Metrics** | Prometheus (prometheus-client, prometheus-fastapi-instrumentator) |
| **Testing** | pytest, httpx, pytest-cov |
| **Linting / formatting** | Ruff |
| **Git hooks** | pre-commit |
| **CI** | GitHub Actions (build/push, manifest validation) |

---

## Quick start

Pick the setup that fits your workflow:

- [Local dev without Docker](#local-dev-no-docker) — fastest to start, SQLite requires no extra services
- [Docker Compose with PostgreSQL](#docker-compose-with-postgresql) — matches production storage, one command
- [Kubernetes](#kubernetes-deployment) — full cluster deployment with split API + NGINX frontend
- [GitOps workflow](#gitops-workflow) — how commits flow from repo to running cluster
- [Monitoring](#monitoring) — Prometheus metrics, Docker Compose and Kubernetes setup

### Local dev (no Docker)

```bash
# 1. Copy environment config
cp .env.example .env

# 2. Install dependencies
uv sync --dev

# 3. Run tests to verify everything works
uv run pytest -v

# 4. Start the server (uses SQLite automatically)
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Open http://localhost:8000/docs for the interactive API docs.
Open http://localhost:8000/static/index.html for the browser UI.

### Docker Compose with PostgreSQL

```bash
# 1. Copy environment config
cp .env.example .env

# 2. Start PostgreSQL + app (builds image; container runs `alembic upgrade head`; starts server)
docker compose up --build

# 3. Verify
curl http://localhost:8000/healthz
```

#### Hot reload during development

Use the dev override to mount source files and restart on save — no rebuild needed:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

> **Windows note:** hot reload uses polling (`WATCHFILES_FORCE_POLLING=true`) for
> reliable file-change detection across the Windows/Linux boundary.

---

## Environment variables

| Variable       | Default                        | Description                                              |
|----------------|--------------------------------|----------------------------------------------------------|
| `DATABASE_URL` | `sqlite:///./flags.db`         | SQLAlchemy connection URL                                |
| `USE_ALEMBIC`  | `false`                        | `true` = skip `create_all`, expect migrations externally |
| `ENVIRONMENT`  | `dev`                          | `dev` / `prod` / `test`                                  |
| `DEBUG`        | `true`                         | Enables SQLAlchemy query logging                         |
| `API_KEY`      | *(empty — auth disabled)*      | Set to enable `X-API-Key` authentication                 |
| `METRICS_ENABLED` | `true`                      | Expose `/metrics` endpoint for Prometheus scraping       |

### Generating an API key

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Add the output to `.env` as `API_KEY=<generated-value>`.
When set, all API routes require the header `X-API-Key: <your-key>`.
The `/healthz` endpoint is always public (required by Docker and Kubernetes probes).

## API reference

> Interactive docs are available at **http://localhost:8000/docs** (Swagger UI) and **http://localhost:8000/redoc** (ReDoc) when the server is running.

All routes require `X-API-Key` header when `API_KEY` is configured.

### Flag object

Every endpoint that returns a flag uses this shape:

```json
{
  "id": 1,
  "app": "demo",
  "env": "dev",
  "key": "dark_mode",
  "value": true,
  "description": "Enable dark mode",
  "version": 2,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T11:00:00Z"
}
```

| Field | Type | Notes |
|-------|------|-------|
| `id` | int | Auto-assigned primary key |
| `app` | string | Application identifier |
| `env` | string | Environment name (`dev`, `prod`, etc.) |
| `key` | string | Flag name — `app + env + key` is unique |
| `value` | bool | Current flag state |
| `description` | string \| null | Optional human-readable label |
| `version` | int | Incremented on every update; required for optimistic locking |
| `created_at` | ISO 8601 | Set once on creation |
| `updated_at` | ISO 8601 | Updated on every write |

### Flags

| Method   | Path             | Description                        |
|----------|------------------|------------------------------------|
| `GET`    | `/flags`         | List flags for an app/env          |
| `GET`    | `/flags/{id}`    | Get a single flag                  |
| `POST`   | `/flags`         | Create a flag                      |
| `PUT`    | `/flags/{id}`    | Update a flag (requires `version`) |
| `DELETE` | `/flags/{id}`    | Delete a flag                      |

Query parameters for `GET /flags`:

| Parameter  | Type | Default | Description                      |
|------------|------|---------|----------------------------------|
| `app_name` | str  | —       | Required. App identifier         |
| `env`      | str  | —       | Required. Environment name       |
| `limit`    | int  | `200`   | Max results. Range: 1–500        |

### Discovery

| Method | Path                      | Description                             |
|--------|---------------------------|-----------------------------------------|
| `GET`  | `/apps`                   | List all distinct app names             |
| `GET`  | `/apps/{app_name}/envs`   | List all environments for an app        |

### Optimistic locking

Updates require the current `version` of the flag. If another client updated the flag between your read and write, the server returns `409 Conflict`. Your client should re-fetch and retry.

```bash
# Read — note the version
curl http://localhost:8000/flags/1
# {"id":1,"version":2,...}

# Update — send the version you read
curl -X PUT http://localhost:8000/flags/1 \
  -H "Content-Type: application/json" \
  -d '{"value":false,"version":2}'
```

> For a complete, always-current request/response reference, use the Swagger UI at **http://localhost:8000/docs** — every endpoint is explorable there with real payloads and live responses.

## Database migrations

This project uses Alembic to version schema changes. Every structural change to the database is a migration file — a recorded, reversible step.

```bash
# Apply all pending migrations
uv run alembic upgrade head

# Roll back the most recent migration
uv run alembic downgrade -1

# Check current migration state
uv run alembic current

# Auto-generate a new migration after changing app/models.py
uv run alembic revision --autogenerate -m "describe your change"
```

> After auto-generating, always review the file in `alembic/versions/` before applying.
> Autogenerate is a starting point, not a final answer.

## Developer setup

```bash
# Install all dependencies including dev tools
uv sync --dev

# Install pre-commit hooks (runs ruff on every commit)
uv run pre-commit install

# Lint and format manually
uv run ruff check --fix .
uv run ruff format .
```

If pre-commit aborts your commit with "files were modified", it means ruff
auto-fixed something. Stage the changes and commit again:

```bash
git add -A
git commit -m "your message"
```

## Running tests

Tests use SQLite by default — no Docker needed.

```bash
# Run all tests
uv run pytest -v

# Run with coverage report
uv run pytest --cov=app --cov-report=term-missing
```

To run tests against PostgreSQL (matches CI exactly):

```bash
# Start PostgreSQL
docker compose up db -d

# Run tests pointing at it
DATABASE_URL=postgresql+psycopg://configserver:configserver@localhost:5432/flags \
  uv run alembic upgrade head && uv run pytest -v
```

---

## GitOps workflow

This project is continuously delivered to a **k3s cluster on Hetzner** using **[Flux CD](https://fluxcd.io/)** — the Git repository is the single source of truth for what runs in the cluster. No one applies manifests manually to the dev environment; Flux continuously reconciles the cluster state against the `main` branch.

### Two-repo architecture

The setup splits responsibility across two repositories:

- **Flux bootstrap repo** (platform-owned) — manages the cluster itself: installs Flux, Istio, and all tenant definitions. It points Flux at this repo and grants it scoped permissions.
- **This repo** (ConfigServer) — owns the application manifests under `k8s/`. Flux watches it and applies changes automatically.

![GitOps deployment pipeline](assets/diagram-gitops-flow.svg)

#### Delivery pipeline — what happens on every push

```mermaid
sequenceDiagram
    actor Dev as 👨‍💻 Developer
    participant GH as GitHub (main)
    participant CI as GitHub Actions
    participant GHCR as GHCR Registry
    participant Flux as Flux CD
    participant K8s as configserver-dev namespace

    Dev->>GH: git push
    GH->>CI: trigger build-push.yml
    CI->>GHCR: push feature-flags-api:sha-XXXXXX
    CI->>GHCR: push feature-flags-frontend:sha-XXXXXX
    CI->>GH: commit "ci: update dev image tags to sha-XXXXXX"

    Note over Flux: syncs GitRepository every 1 min
    Flux->>GH: fetch new revision
    GH-->>Flux: k8s/feature-flags/overlays/dev/ + encrypted secrets
    Note over Flux: decrypt SOPS secrets using age key
    Flux->>K8s: apply Kustomize overlay (prune enabled)
    K8s->>GHCR: pull new images
    Note over K8s: rolling update — old pods replaced
```

### How it works step by step

1. **Push to `main`** — any commit (code change, manifest edit, secret rotation) triggers the CI pipeline.
2. **CI builds and pushes images** — GitHub Actions builds the API and frontend Docker images, tags them with the short commit SHA (`sha-XXXXXX`), and pushes them to GHCR.
3. **CI writes back to the repo** — the pipeline patches `k8s/feature-flags/overlays/dev/kustomization.yaml` with the new image tags and commits `ci: update dev image tags to sha-XXXXXX`. The manifest always reflects exactly what image is running.
4. **Flux detects the change** — the Flux `GitRepository` resource polls `github.com/pmiloszz/ConfigServer` every **1 minute**. On a new commit it fetches the latest tree.
5. **Flux reconciles** — the `configserver-dev` Flux `Kustomization` applies `k8s/feature-flags/overlays/dev/` every **10 minutes** (triggered immediately on a new source revision). Before applying, Flux decrypts any SOPS-encrypted files using the `age` private key stored as a cluster secret.
6. **Scoped deployment** — Flux acts as the `flux-tenant` ServiceAccount, which has RBAC permission only in the `configserver-dev` and `configserver-prod` namespaces. It cannot touch other tenants or platform components.
7. **Traffic routing** — an Istio Gateway with a Gateway API `HTTPRoute` routes `configserver-dev.501404.xyz` HTTPS traffic to the NGINX frontend Service, which proxies API calls to the FastAPI pod over internal ClusterIP.
8. **Pruning** — if a resource is removed from the repo, Flux deletes it from the cluster on the next reconciliation (`prune: true`). No orphaned resources accumulate.

### Key properties

| Property | Detail |
|----------|--------|
| **GitOps controller** | [Flux CD](https://fluxcd.io/) v2 |
| **Cluster** | k3s on Hetzner |
| **Trigger** | Every push to `main` |
| **Poll interval** | `GitRepository`: 1 min · `Kustomization`: 10 min |
| **Image registry** | GitHub Container Registry (GHCR) |
| **Image tagging** | Short commit SHA (`sha-XXXXXX`) — every build is uniquely traceable |
| **Manifest path (dev)** | `k8s/feature-flags/overlays/dev/` → namespace `configserver-dev` |
| **Manifest path (prod)** | `k8s/feature-flags/overlays/prod/` → namespace `configserver-prod` *(not yet active)* |
| **Secret management** | SOPS + `age` — secrets encrypted in repo, decrypted by Flux at apply time |
| **Tenant isolation** | `flux-tenant` ServiceAccount; RBAC scoped to `configserver-*` namespaces only |
| **Ingress** | Istio Gateway + Gateway API `HTTPRoute` |
| **Pruning** | Enabled — resources deleted from repo are removed from cluster |

> The `local` overlay (`k8s/feature-flags/overlays/local/`) is **not** managed by Flux — it is applied manually with `kubectl apply -k` for local development on Docker Desktop.

---

## Monitoring

The API exposes a `/metrics` endpoint in Prometheus text format (enabled by default, controlled via `METRICS_ENABLED`).

### Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `configserver_flag_list_requests_total` | Counter | `app`, `env` | Total flag list requests |
| `configserver_flags_returned` | Histogram | `app`, `env` | Number of flags returned per list request |
| `configserver_flag_list_at_limit_total` | Counter | `app`, `env` | List requests that hit the result limit (possible truncation) |
| `configserver_flag_writes_total` | Counter | `operation` | Flag create / update / delete operations |
| `configserver_flag_value_changes_total` | Counter | `app`, `env`, `direction` | Flag value toggles (`enable` / `disable`) |
| `configserver_version_conflicts_total` | Counter | — | Optimistic concurrency conflicts (409) |
| `configserver_auth_failures_total` | Counter | `reason` | Authentication failures (`missing` / `invalid`) |
| `http_request_duration_seconds` | Histogram | `handler`, `method`, `status` | Per-endpoint HTTP latency (from `prometheus-fastapi-instrumentator`) |

### Local Docker Compose

Prometheus is included in `docker-compose.yml` and starts automatically:

```bash
docker compose up
# Prometheus UI → http://localhost:9090
```

The scrape config lives in `prometheus.yml` at the repo root.

### Kubernetes

A Prometheus deployment is provided in `k8s/monitoring/base/`. It runs in the `monitoring` namespace and scrapes the API over the internal ClusterIP DNS name — no NodePort or ingress required.

```bash
# Deploy
kubectl apply -k k8s/monitoring/base

# Access the UI via port-forward
kubectl port-forward -n monitoring svc/prometheus-svc 9090:9090
# then open http://localhost:9090
```

### Useful PromQL queries

```promql
# Request rate per app/env (last 5 min)
rate(configserver_flag_list_requests_total[5m])

# Average flags returned per request
rate(configserver_flags_returned_sum[5m]) / rate(configserver_flags_returned_count[5m])

# p99 API latency across all endpoints
histogram_quantile(0.99, sum by (le) (rate(http_request_duration_highr_seconds_bucket[5m])))

# Auth failures by reason
configserver_auth_failures_total

# Concurrent write conflicts
increase(configserver_version_conflicts_total[1h])
```

---

## Kubernetes deployment

The `k8s/feature-flags/` directory contains the current Kubernetes manifests (Kustomize base + overlays).

### Architecture

The deployment uses two containers so that static file serving stays out of the Python process and each component can scale independently:

- **`feature-flags-api`** — FastAPI application; handles all `/flags`, `/apps`, and `/healthz` requests.
- **`feature-flags-frontend`** — NGINX serving the static browser UI and reverse-proxying API routes to the API service.

```
LoadBalancer / Ingress
        │
        ▼
┌──────────────────────┐
│  NGINX frontend  :80 │
│  /static/*  ─────────┼──► serves HTML/CSS/JS directly
│  /flags/*   ─────────┤
│  /apps/*    ─────────┼──► feature-flags-api-svc :8000
│  /healthz   ─────────┤    (FastAPI + PostgreSQL)
└──────────────────────┘
```

### Prerequisites

- A running cluster (minikube, kind, EKS, GKE, AKS)
- `kubectl` configured to point at it
- Your container image pushed to a registry

### Steps

```bash
# 1. Build and push your images
docker build -t your-registry.io/feature-flags-api:latest .
docker push your-registry.io/feature-flags-api:latest

docker build -t your-registry.io/feature-flags-frontend:latest -f frontend/Dockerfile .
docker push your-registry.io/feature-flags-frontend:latest

# 2. Update image tags and credentials
#    - Image tags are configured in `k8s/feature-flags/overlays/<env>/kustomization.yaml` (`images:` section).
#    - Secret placeholders are in `k8s/feature-flags/base/feature-flags-secret.yaml`.

# 3. Apply manifests
kubectl apply -k k8s/feature-flags/overlays/dev
# or
kubectl apply -k k8s/feature-flags/overlays/prod

# 4. Check everything is running
kubectl get all -n feature-flags

# 5. Access locally (dev/prod overlays use LoadBalancer on the frontend Service)
# kubectl get svc -n feature-flags feature-flags-svc
# Then open http://<EXTERNAL-IP>/static/index.html (Docker Desktop often uses localhost)
```

### Useful kubectl commands

```bash
# Watch pods come up
kubectl get pods -n feature-flags -w

# Check app logs
kubectl logs -n feature-flags deployment/feature-flags-api -f

# Check postgres logs
kubectl logs -n feature-flags statefulset/postgres -f

# Run a migration manually
kubectl exec -n feature-flags deployment/feature-flags-api -- alembic upgrade head

# Connect to postgres directly
kubectl exec -it -n feature-flags statefulset/postgres -- psql -U configserver -d flags
```

---

## Project structure

```
ConfigServer/
├── .github/
│   └── workflows/           # CI pipelines (build/push, manifest validation, tests)
├── app/
│   ├── api/
│   │   ├── apps.py          # Discovery endpoints (/apps, /apps/{app}/envs)
│   │   └── flags.py         # CRUD endpoints (/flags)
│   ├── repositories/
│   │   ├── flag_repository.py       # Concrete SQLModel implementation
│   │   └── flag_repository_base.py  # Abstract base (enables test mocking)
│   ├── services/
│   │   ├── exceptions.py    # Domain exceptions (FlagNotFound, VersionConflict...)
│   │   └── flag_service.py  # Business logic
│   ├── schemas/
│   │   └── flag.py          # Pydantic request/response models
│   ├── auth.py              # API key dependency
│   ├── db.py                # Engine and session factory
│   ├── metrics.py           # Prometheus metric singletons
│   ├── models.py            # SQLModel ORM model
│   └── settings.py          # Pydantic settings (reads from .env)
├── alembic/
│   └── versions/            # Migration files — one per schema change
├── frontend/                # NGINX image for K8s (serves static/, proxies API)
├── k8s/
│   ├── feature-flags/       # App manifests (Kustomize base + overlays)
│   └── monitoring/          # Prometheus deployment (namespace, ConfigMap, Deployment, ClusterIP Service)
├── scripts/
│   └── test_db.py           # Isolated SQLite fixtures for direct service-layer testing
├── static/
│   ├── index.html           # Browser UI shell
│   ├── app.js               # UI logic (fetch API)
│   └── styles.css           # UI styles
├── tests/
│   ├── conftest.py          # Shared fixtures (SQLite locally, PostgreSQL in CI)
│   ├── test_apps_api.py
│   ├── test_auth.py
│   ├── test_flag_repository.py
│   ├── test_flag_service.py
│   └── test_flags_api.py
├── docker-compose.yml       # Production Compose (includes Prometheus service)
├── docker-compose.dev.yml   # Dev override (hot reload)
├── prometheus.yml           # Prometheus scrape config (Docker Compose)
├── Dockerfile
└── main.py                  # App factory and lifespan handler
```
