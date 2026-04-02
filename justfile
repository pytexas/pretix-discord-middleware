# ABOUTME: Build automation for the pretix-discord project.
# Provides targets for linting, type-checking, testing, and formatting.

default: check

check: fmt test lint typecheck

fmt:
    uv run ruff format src tests

lint:
    uv run ruff check src tests

typecheck:
    uv run mypy src tests

test:
    uv run pytest tests -v

all: check
