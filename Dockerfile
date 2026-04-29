# syntax=docker/dockerfile:1.7
#
# Multi-stage build for agentic-control v0.
#
# Stages:
#   deps    — install locked dependencies (cached on uv.lock changes only)
#   dev     — add the project + test deps, used as base for test/smoke
#   test    — ruff + pytest; build fails iff lint or any test fails
#   smoke   — alembic upgrade + scripts/smoke.sh end-to-end exercise
#   runtime — slim final image with agentctl entrypoint
#
# Common targets:
#   docker build --target test  .            # run quality gate
#   docker build --target smoke .            # full E2E smoke
#   docker build --target runtime -t agentctl:v0 .
#   docker run --rm -v $HOME/.agentic-control:/data agentctl:v0 work next

ARG UV_VERSION=0.11
ARG PYTHON_VERSION=3.14

# ---------- deps ----------
FROM ghcr.io/astral-sh/uv:${UV_VERSION}-python${PYTHON_VERSION}-bookworm-slim AS deps

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/opt/venv

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# ---------- dev ----------
FROM deps AS dev

COPY src ./src
COPY migrations ./migrations
COPY alembic.ini ./
COPY tests ./tests
COPY scripts ./scripts

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

ENV PATH="/opt/venv/bin:${PATH}"

# ---------- test ----------
FROM dev AS test

RUN ruff check && pytest -q

# ---------- smoke ----------
FROM dev AS smoke

ENV SMOKE_DB_DIR=/tmp/agentctl-smoke
RUN scripts/smoke.sh

# ---------- runtime ----------
FROM python:${PYTHON_VERSION}-slim-bookworm AS runtime

# sqlite3 CLI for diagnostics (tiny); rest comes from the venv.
RUN apt-get update \
 && apt-get install -y --no-install-recommends sqlite3 \
 && rm -rf /var/lib/apt/lists/*

COPY --from=deps /opt/venv /opt/venv
COPY --from=dev /app/src /app/src
COPY --from=dev /app/migrations /app/migrations
COPY --from=dev /app/alembic.ini /app/alembic.ini

ENV PATH="/opt/venv/bin:${PATH}" \
    PYTHONPATH="/app/src" \
    AGENTIC_CONTROL_DB_URL="sqlite:////data/state.db"

WORKDIR /app

# Install the project itself into the runtime venv (without dev deps).
COPY pyproject.toml /app/
RUN /opt/venv/bin/pip install --no-deps --no-cache-dir -e /app

# State volume — caller mounts a host path to persist between runs.
VOLUME ["/data"]

ENTRYPOINT ["agentctl"]
CMD ["--help"]
