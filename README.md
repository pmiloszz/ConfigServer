# ConfigServer

**ConfigServer** is a lightweight HTTP service for managing feature flags. It provides CRUD operations for flags, optimistic versioning for updates, and database migrations via Alembic. The project is prepared for local development and containerized deployment with Docker.

## Quick start (local)

1. Copy the example environment file
```bash
cp .env.example .env
```
2. Install depencecies
```
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```
3. Run database migrations
```
python -m alembic upgrade head
```
4. Start the server
```bash
uv run uvicorn main:app --host 0.0.0.0 --port 8000
# or
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```
5. Verify
+ OpenAPI UI: http://127.0.0.1:8000/docs
+ Health endpoint: http://127.0.0.1:8000/health

##Environment configuration
Files

.env — local environment values, do not commit.

.env.example — example variables to keep in the repository.

Key variables

DATABASE_URL — e.g. sqlite:///./flags.db or postgresql+psycopg2://user:pass@host/db

USE_ALEMBIC — true or false

ENVIRONMENT — dev / prod / test

### Example .env.example
DATABASE_URL=sqlite:///./flags.db
USE_ALEMBIC=false
ENVIRONMENT=dev
DEBUG=true

## Using CRUD options
### Get
```bash
#list
curl -sS "http://127.0.0.1:8000/flags?app_name=demo&env=dev"
#by flag
curl -sS "http://127.0.0.1:8000/flags/1"
```

### Post
```bash
curl -sS -X POST http://127.0.0.1:8000/flags \
  -H "Content-Type: application/json" \
  -d '{"app":"demo","env":"dev","key":"feature_z","value":true,"description":"test"}'"
```
### Put
```bash
curl -sS -X PUT http://127.0.0.1:8000/flags/1 \
  -H "Content-Type: application/json" \
  -d '{"value":false,"description":"turned off","version":2}'
```
### Delete
```bash
curl -sS -X DELETE http://127.0.0.1:8000/flags/3 -i
```

# Requirements
- uv package manager [link](https://docs.astral.sh/uv/getting-started/installation/#scoop)
