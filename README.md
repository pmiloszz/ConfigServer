# ConfigServer

A lightweight HTTP service for managing feature flags. Flags are stored per application, environment, and key with optimistic locking to prevent conflicting updates.

## Features

- Full CRUD for feature flags
- Optimistic locking via `version` field — concurrent updates conflict safely
- Discovery endpoints — list apps and environments without prior knowledge
- Optional API key authentication via `X-API-Key` header
- Browser UI at `/static/index.html` — toggle, create, edit, delete, search
- PostgreSQL in production, SQLite for local dev and tests
- Alembic migrations — schema changes are versioned and repeatable
- Docker Compose for local dev (with hot reload) and production
- Kubernetes manifests for cluster deployment

---

## Quick start — local dev (no Docker)

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

---

## Quick start — Docker Compose with PostgreSQL

```bash
# 1. Copy environment config
cp .env.example .env

# 2. Start PostgreSQL + app (builds image; container runs `alembic upgrade head`; starts server)
docker compose up --build

# 3. Verify
curl http://localhost:8000/healthz
```

### Hot reload during development

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
| `DATABASE_URL` | `sqlite:///./flags.db`        | SQLAlchemy connection URL                                |
| `USE_ALEMBIC`  | `false`                        | `true` = skip `create_all`, expect migrations externally |
| `ENVIRONMENT`  | `dev`                          | `dev` / `prod` / `test`                                  |
| `DEBUG`        | `true`                         | Enables SQLAlchemy query logging                         |
| `API_KEY`      | *(empty — auth disabled)*      | Set to enable `X-API-Key` authentication                 |

### Generating an API key

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Add the output to `.env` as `API_KEY=<generated-value>`.
When set, all API routes require the header `X-API-Key: <your-key>`.
The `/healthz` endpoint is always public (required by Docker and Kubernetes probes).

---

## API reference

All routes require `X-API-Key` header when `API_KEY` is configured.

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

### Example curl commands

```bash
# List flags
curl "http://localhost:8000/flags?app_name=demo&env=dev"

# Create a flag
curl -X POST http://localhost:8000/flags \
  -H "Content-Type: application/json" \
  -d '{"app":"demo","env":"dev","key":"dark_mode","value":true,"description":"Enable dark mode"}'

# Toggle a flag off
curl -X PUT http://localhost:8000/flags/1 \
  -H "Content-Type: application/json" \
  -d '{"value":false,"version":1}'

# Delete a flag
curl -X DELETE http://localhost:8000/flags/1

# With API key enabled
curl -H "X-API-Key: your-key-here" "http://localhost:8000/flags?app_name=demo&env=dev"
```

---

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

### Migration history

| Revision       | Description              |
|----------------|--------------------------|
| `5620a60df499` | Initial schema           |
| `b3d4e5f6a7b8` | Add `created_at` to flag |

---

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

---

## Kubernetes deployment

The `k8s/` directory contains manifests for deploying to any Kubernetes cluster.

### Prerequisites

- A running cluster (minikube, kind, EKS, GKE, AKS)
- `kubectl` configured to point at it
- Your container image pushed to a registry

### Steps

```bash
# 1. Build and push your image
docker build -t your-registry.io/configserver:latest .
docker push your-registry.io/configserver:latest

# 2. Update the image reference in k8s/06-app-deployment.yaml
#    Replace: your-registry.io/configserver:latest

# 3. Set real credentials in k8s/01-secret.yaml
#    echo -n "your-password" | base64

# 4. Apply in order
kubectl apply -f k8s/00-namespace.yaml
kubectl apply -f k8s/01-secret.yaml
kubectl apply -f k8s/02-configmap.yaml
kubectl apply -f k8s/03-postgres-pvc.yaml
kubectl apply -f k8s/04-postgres-statefulset.yaml
kubectl apply -f k8s/05-postgres-service.yaml
kubectl apply -f k8s/06-app-deployment.yaml
kubectl apply -f k8s/07-app-service.yaml

# Or apply the whole directory at once
kubectl apply -f k8s/

# 5. Check everything is running
kubectl get all -n configserver

# 6. On minikube — get the external URL
minikube service configserver-service -n configserver
```

### Useful kubectl commands

```bash
# Watch pods come up
kubectl get pods -n configserver -w

# Check app logs
kubectl logs -n configserver deployment/configserver -f

# Check postgres logs
kubectl logs -n configserver statefulset/postgres -f

# Run a migration manually
kubectl exec -n configserver deployment/configserver -- alembic upgrade head

# Connect to postgres directly
kubectl exec -it -n configserver statefulset/postgres -- psql -U configserver -d flags
```

---

## Project structure

```
configserver/
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
│   ├── models.py            # SQLModel ORM model
│   └── settings.py          # Pydantic settings (reads from .env)
├── alembic/
│   └── versions/            # Migration files — one per schema change
├── k8s/                     # Kubernetes manifests
├── static/
│   └── index.html           # Browser UI
├── tests/
│   ├── conftest.py          # Shared fixtures (SQLite locally, PostgreSQL in CI)
│   ├── test_apps_api.py
│   ├── test_auth.py
│   ├── test_flag_repository.py
│   ├── test_flag_service.py
│   └── test_flags_api.py
├── docker-compose.yml       # Production Compose
├── docker-compose.dev.yml   # Dev override (hot reload)
├── Dockerfile
└── main.py                  # App factory and lifespan handler
```