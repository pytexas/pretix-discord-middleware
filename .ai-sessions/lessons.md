# Lessons Learned

## Recent
<!-- 10 most recent lessons, newest first -->

- Load all relevant skills (temporal-developer, python) before writing any code, not after implementation (2026-03-30)
- Pure logic functions (no I/O, deterministic) should be plain functions called in the workflow, not Temporal activities (2026-03-30)
- Always include [build-system] in pyproject.toml when scaffolding Python projects with uv — `uv sync` needs it to install the package (2026-03-30)
- Temporal's default RetryPolicy is sufficient for most cases — don't add custom retry config without a domain-specific reason (2026-03-30)
- Separate dataclasses/models into their own file (models.py) rather than mixing with activity implementations (2026-03-30)
- Name activity files with the pattern `*_activities.py` (e.g., pretix_activities.py, discord_activities.py) for clarity (2026-03-30)
- Use `WorkflowEnvironment.start_local()` for Temporal tests without timers; `start_time_skipping()` is only needed for workflows with durable sleeps (2026-03-30)
- Use unique UUIDs for task queue names and workflow IDs in Temporal tests to avoid conflicts (2026-03-30)
- The temporalio/auto-setup Docker image is deprecated — use temporalio/temporal:latest with `server start-dev` and a mounted SQLite volume (2026-03-30)
- For async httpx activities in Temporal, no ThreadPoolExecutor is needed — only sync activities require one (2026-03-30)

## Categories
<!-- Lessons organized by topic -->

### Temporal
- Pure logic functions (no I/O, deterministic) should be plain functions called in the workflow, not Temporal activities (2026-03-30)
- Temporal's default RetryPolicy is sufficient for most cases — don't add custom retry config without a domain-specific reason (2026-03-30)
- Use `WorkflowEnvironment.start_local()` for Temporal tests without timers; `start_time_skipping()` is only needed for workflows with durable sleeps (2026-03-30)
- Use unique UUIDs for task queue names and workflow IDs in Temporal tests to avoid conflicts (2026-03-30)
- The temporalio/auto-setup Docker image is deprecated — use temporalio/temporal:latest with `server start-dev` and a mounted SQLite volume (2026-03-30)
- For async httpx activities in Temporal, no ThreadPoolExecutor is needed — only sync activities require one (2026-03-30)

### Python
- Always include [build-system] in pyproject.toml when scaffolding Python projects with uv — `uv sync` needs it to install the package (2026-03-30)
- Separate dataclasses/models into their own file (models.py) rather than mixing with activity implementations (2026-03-30)
- Name activity files with the pattern `*_activities.py` (e.g., pretix_activities.py, discord_activities.py) for clarity (2026-03-30)

### Workflow
- Load all relevant skills (temporal-developer, python) before writing any code, not after implementation (2026-03-30)
