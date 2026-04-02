# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
just check       # Run all checks: fmt, test, lint, typecheck
just fmt          # Format code with ruff
just test         # Run all tests
just lint         # Lint with ruff
just typecheck    # Type check with mypy --strict

# Run a single test file
uv run pytest tests/test_pretix.py -v

# Run a single test
uv run pytest tests/test_pretix.py::TestParsePretixOrder::test_extracts_order_fields -v

# Install dependencies
uv sync
```

## Architecture

This is a webhook middleware: pretix (ticket platform) sends webhook POSTs when orders are placed, and this service fetches the order details and posts a formatted embed to Discord.

The pipeline is orchestrated by Temporal for durable execution with automatic retries.

```
pretix --POST--> FastAPI (api.py) --starts workflow--> Temporal
                                                         |
                                           fetch_pretix_order (activity)
                                                         |
                                           format_discord_embed (plain function)
                                                         |
                                           send_discord_webhook (activity)
```

### Key design decisions

- **models.py** holds all dataclasses. Activity files import from it, not the other way around.
- **`*_activities.py`** naming convention for files containing Temporal activities.
- **`format_discord_embed`** is a plain function, not a Temporal activity — it's pure deterministic logic with no I/O, so it runs directly in the workflow.
- **Async activities** use `httpx.AsyncClient` (async-safe). No `ThreadPoolExecutor` needed.
- **Default Temporal RetryPolicy** — no custom retry config unless there's a domain-specific reason.
- **Workflow file** (`workflow.py`) imports activities and models through `workflow.unsafe.imports_passed_through()` for sandbox compatibility. Keep this file minimal.

### Temporal specifics

- Workflow and activity definitions must be in separate files (sandbox reloads workflow files on every execution).
- Activities do I/O (HTTP calls). Workflows only orchestrate.
- Tests use `WorkflowEnvironment.start_local()` with mocked activities and unique UUID task queues.
- Worker entrypoint: `python -m pretix_discord.worker`
- Web entrypoint: `python -m pretix_discord.main`

### Pretix API shape

The pretix order response does **not** include item names on positions — `item` and `variation` are numeric IDs. `fetch_pretix_order` makes two concurrent requests: one for the order, one for the event's `/items/` catalog. `_build_item_lookups()` converts the items response into `{id: name}` dicts that `parse_pretix_order()` uses for display.

### Deployment

Docker Compose with four services: Caddy (HTTPS), Temporal CLI dev server (SQLite), worker, web. Configuration via environment variables (see `.env.example`).

- `uv.lock` is committed — required for reproducible Docker builds.
- The `caddy` service must have `env_file: .env` so `$DOMAIN` expands correctly in the Caddyfile.
- Temporal ports (`7233`, `8233`) are bound to `127.0.0.1` only — not publicly exposed.
- The Temporal SQLite volume mount requires world-writable permissions (`chmod 777`) on the host data directory.
