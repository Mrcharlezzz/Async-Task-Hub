ARG PYTHON_IMAGE=python:3.11-slim

# Common base with shared environment configuration.
FROM ${PYTHON_IMAGE} AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

# Builder stage installs project dependencies once.
FROM base AS builder

COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --upgrade pip \
 && pip install --no-cache-dir .

# API runtime image.
FROM base AS api

COPY --from=builder /usr/local /usr/local
COPY --from=builder /app /app

EXPOSE 8000

CMD ["uvicorn", "src.api.presentation.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Worker runtime image (also used by Flower via docker-compose overrides).
FROM base AS worker

COPY --from=builder /usr/local /usr/local
COPY --from=builder /app /app

CMD ["celery", "-A", "src.api.infrastructure.celery.app:celery_app", "worker", "-l", "INFO", "--concurrency", "1"]
