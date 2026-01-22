ARG PYTHON_IMAGE=python:3.11-slim

# Common base with shared environment configuration.
FROM ${PYTHON_IMAGE} AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    PYTHONPATH=/app

WORKDIR /app

COPY entrypoint.sh /entrypoint.sh

# Builder stage installs project dependencies once.
FROM base AS builder

COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --upgrade pip \
 && pip install --no-cache-dir .

# Test image with optional dependencies.
FROM base AS test

COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --upgrade pip \
 && pip install --no-cache-dir ".[test]"

# Runtime image without DB migrations (used by non-DB services).
FROM base AS runtime

COPY --from=builder /usr/local /usr/local
COPY --from=builder /app /app

# API runtime image (runs DB migrations).
FROM runtime AS api

EXPOSE 8000

RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["uvicorn", "src.app.presentation.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Worker runtime image (no DB migrations).
FROM runtime AS worker

CMD ["celery", "-A", "src.app.infrastructure.celery.app:celery_app", "worker", "-l", "INFO", "--concurrency", "1"]
