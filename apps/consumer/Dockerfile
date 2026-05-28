FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.8.22 /uv /uvx /bin/

WORKDIR /workspace

RUN addgroup --system dealmoa && adduser --system --ingroup dealmoa dealmoa

COPY pyproject.toml ./
COPY uv.lock ./
COPY apps/api/pyproject.toml apps/api/pyproject.toml
COPY apps/consumer/pyproject.toml apps/consumer/pyproject.toml
COPY apps/worker/pyproject.toml apps/worker/pyproject.toml

RUN uv sync --package dealmoa-consumer --no-dev

COPY --chown=dealmoa:dealmoa apps/api/app apps/api/app
COPY --chown=dealmoa:dealmoa apps/consumer apps/consumer

USER dealmoa

ENV PYTHONPATH=/workspace/apps/api:/workspace/apps/consumer

CMD ["uv", "run", "python", "-m", "consumer_app.main", "publish-outbox"]
