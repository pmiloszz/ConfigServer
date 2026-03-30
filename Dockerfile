# --- Builder ---
FROM ghcr.io/astral-sh/uv:python3.14-trixie-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NO_DEV=1 \
    UV_PYTHON_DOWNLOADS=0 \
    UV_PROJECT_ENVIRONMENT=/opt/venv

WORKDIR /app

# Install dependencies first (cached layer).
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project

COPY . /app

# Install the project (non-editable) into the image venv.
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-editable

# --- Runtime ---
FROM python:3.14-slim-trixie

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app
EXPOSE 8000

# Copy only runtime inputs (avoid shipping repo metadata like README/uv.lock).
COPY --from=builder /app/app /app/app
COPY --from=builder /app/alembic /app/alembic
COPY --from=builder /app/alembic.ini /app/alembic.ini
COPY --from=builder /app/main.py /app/main.py
COPY --from=builder /app/docker-entrypoint.sh /app/docker-entrypoint.sh
COPY --from=builder /opt/venv /opt/venv

# Default command: run migrations then start server
CMD ["sh", "/app/docker-entrypoint.sh"]