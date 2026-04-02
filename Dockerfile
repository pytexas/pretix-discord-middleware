# ABOUTME: Multi-stage Dockerfile for the pretix-discord middleware.
# Builds with uv and produces a slim runtime image.

FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY src/ src/
RUN uv sync --frozen --no-dev

FROM python:3.13-slim-bookworm AS runtime

WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY src/ src/

ENV PATH="/app/.venv/bin:$PATH"
