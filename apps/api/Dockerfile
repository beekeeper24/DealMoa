FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.8.22 /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /workspace

RUN addgroup --system dealmoa && adduser --system --ingroup dealmoa dealmoa

COPY pyproject.toml ./
COPY uv.lock ./
COPY apps/api/pyproject.toml apps/api/pyproject.toml
RUN uv sync --package dealmoa-api --no-dev

COPY --chown=dealmoa:dealmoa apps/api apps/api

WORKDIR /workspace/apps/api
USER dealmoa

CMD ["/workspace/.venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
