# Lessons Learned

## Recent
<!-- 10 most recent lessons, newest first -->

- `${VAR:?err}` interpolation in docker-compose fires at parse time for every command including `build` — use `env_file:` for runtime-only secrets instead (2026-04-16)
- `temporalio/temporal:latest` is alpine-based with sh but no curl — `apk add --no-cache curl` to bootstrap installers (2026-04-16)
- `usermod -aG docker` doesn't affect running shells; use `newgrp docker` or full logout to pick up new supplementary groups (2026-04-16)
- Prefer reusing the upstream image as the Dockerfile base instead of writing a parallel builder stage — less to maintain and closer to upstream (2026-04-16)
- Always verify external API field names against actual docs before writing mock data — inferring field names from context leads to bugs that only surface in production (2026-03-30)
- uv.lock should never be gitignored — Docker builds and CI need it for reproducible installs (2026-03-30)
- In Docker Compose, every service that uses env vars must have env_file explicitly — it does not inherit from other services (2026-03-30)
- Temporal's "attempt N" in logs is just a counter, not a max-retry warning — default RetryPolicy has unlimited retries (2026-03-30)
- Bind sensitive internal ports (Temporal gRPC/UI) to 127.0.0.1 in Docker Compose to prevent public exposure (2026-03-30)
- Load all relevant skills (temporal-developer, python) before writing any code, not after implementation (2026-03-30)

## Categories
<!-- Lessons organized by topic -->

### Temporal
- Pure logic functions (no I/O, deterministic) should be plain functions called in the workflow, not Temporal activities (2026-03-30)
- Temporal's default RetryPolicy is sufficient for most cases — don't add custom retry config without a domain-specific reason (2026-03-30)
- Temporal's "attempt N" in logs is just a counter, not a max-retry warning — default RetryPolicy has unlimited retries (2026-03-30)
- Use `WorkflowEnvironment.start_local()` for Temporal tests without timers; `start_time_skipping()` is only needed for workflows with durable sleeps (2026-03-30)
- Use unique UUIDs for task queue names and workflow IDs in Temporal tests to avoid conflicts (2026-03-30)
- The temporalio/auto-setup Docker image is deprecated — use temporalio/temporal:latest with `server start-dev` and a mounted SQLite volume (2026-03-30)
- For async httpx activities in Temporal, no ThreadPoolExecutor is needed — only sync activities require one (2026-03-30)

### Python
- Always include [build-system] in pyproject.toml when scaffolding Python projects with uv — `uv sync` needs it to install the package (2026-03-30)
- uv.lock should never be gitignored — Docker builds and CI need it for reproducible installs (2026-03-30)
- Separate dataclasses/models into their own file (models.py) rather than mixing with activity implementations (2026-03-30)
- Name activity files with the pattern `*_activities.py` (e.g., pretix_activities.py, discord_activities.py) for clarity (2026-03-30)

### Testing
- Always verify external API field names against actual docs before writing mock data — inferring field names from context leads to bugs that only surface in production (2026-03-30)

### Docker
- In Docker Compose, every service that uses env vars must have env_file explicitly — it does not inherit from other services (2026-03-30)
- Bind sensitive internal ports (Temporal gRPC/UI) to 127.0.0.1 in Docker Compose to prevent public exposure (2026-03-30)
- SQLite volume mounts for Temporal need world-writable permissions (chmod 777) when the container runs as non-root (2026-03-30)
- `${VAR:?err}` interpolation in docker-compose fires at parse time for every command including `build` — use `env_file:` for runtime-only secrets instead (2026-04-16)
- `temporalio/temporal:latest` is alpine-based with sh but no curl — `apk add --no-cache curl` to bootstrap installers (2026-04-16)
- Prefer reusing the upstream image as the Dockerfile base instead of writing a parallel builder stage — less to maintain and closer to upstream (2026-04-16)

### Tooling
- `usermod -aG docker` doesn't affect running shells; use `newgrp docker` or full logout to pick up new supplementary groups (2026-04-16)

### Workflow
- Load all relevant skills (temporal-developer, python) before writing any code, not after implementation (2026-03-30)
