FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.8.22 /uv /uvx /bin/

WORKDIR /workspace

RUN addgroup --system dealmoa && adduser --system --ingroup dealmoa dealmoa

COPY pyproject.toml ./
COPY uv.lock ./
COPY apps/api/pyproject.toml apps/api/pyproject.toml
COPY apps/consumer/pyproject.toml apps/consumer/pyproject.toml
COPY apps/worker/pyproject.toml apps/worker/pyproject.toml

RUN uv sync --package dealmoa-worker --no-dev

COPY --chown=dealmoa:dealmoa apps/worker apps/worker

USER dealmoa

ENV PYTHONPATH=/workspace/apps/worker

CMD ["uv", "run", "celery", "-A", "worker_app.celery_app:celery_app", "worker", "--loglevel=INFO"]
