# Pretix-to-Discord Middleware — TODO

## Step 1: Project Scaffolding & Configuration
- [x] Write config validation tests (tests/test_config.py)
- [x] Create pyproject.toml with dependencies
- [x] Create justfile with check/fmt/test targets
- [x] Create project structure (src/pretix_discord/, tests/)
- [x] Implement Settings dataclass and load_config() in src/pretix_discord/config.py
- [x] Verify: `just check` passes

## Step 2: Pretix API Client Activity
- [x] Write parse_pretix_order() tests (tests/test_pretix.py)
- [x] Implement PretixOrder dataclass and parse_pretix_order()
- [x] Write fetch_pretix_order activity tests with respx mocks
- [x] Implement fetch_pretix_order Temporal activity
- [x] Verify: `just check` passes

## Step 3: Discord Embed Formatter Activity
- [x] Write format_discord_embed() tests (tests/test_discord.py)
- [x] Implement Discord payload dataclasses and format_discord_embed activity
- [x] Verify: `just check` passes

## Step 4: Discord Webhook Sender Activity
- [x] Write send_discord_webhook() tests (tests/test_discord_sender.py)
- [x] Implement send_discord_webhook Temporal activity
- [x] Verify: `just check` passes

## Step 5: Temporal Workflow Orchestration
- [x] Write PretixWebhookWorkflow tests with mocked activities (tests/test_workflow.py)
- [x] Implement PretixWebhookWorkflow in src/pretix_discord/workflow.py
- [x] Verify: `just check` passes

## Step 6: FastAPI Webhook Endpoint
- [x] Write webhook endpoint tests (tests/test_api.py)
- [x] Implement FastAPI app with POST /webhook and GET /health
- [x] Verify: `just check` passes

## Step 7: Worker Entrypoint & End-to-End Wiring
- [x] Create worker entrypoint (src/pretix_discord/worker.py)
- [x] Create web server entrypoint (src/pretix_discord/main.py)
- [x] Create Dockerfile
- [x] Create docker-compose.yml and .env.example
- [x] Run full verification: `just check`
- [ ] Document smoke test procedure
