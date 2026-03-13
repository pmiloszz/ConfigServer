#!/usr/bin/env sh
set -e

# If USE_ALEMBIC env var is true, run migrations
if [ "${USE_ALEMBIC:-false}" = "true" ]; then
  echo "Running Alembic migrations..."
  alembic upgrade head
fi

# Start the app (use uv if you prefer)
exec uvicorn main:app --host 0.0.0.0 --port 8000
