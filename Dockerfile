# Use official Python 3.14 slim image
FROM python:3.14-slim

# Working directory
WORKDIR /app

# Prevent Python from writing .pyc files and enable stdout/stderr buffering
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system deps (sqlite tools optional)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency metadata first to leverage Docker cache
COPY pyproject.toml pyproject.toml
COPY requirements.txt requirements.txt

# Install runtime dependencies
RUN python -m pip install --upgrade pip setuptools wheel
RUN pip install -r requirements.txt

# Copy application code
COPY . .

# Make entrypoint executable if provided
RUN chmod +x /app/docker-entrypoint.sh || true

EXPOSE 8000

# Default command: run migrations then start server
CMD ["sh", "/app/docker-entrypoint.sh"]