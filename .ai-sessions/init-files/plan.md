# Pretix-to-Discord Middleware — Implementation Plan

## Current Status

| Step | Description | Status |
|------|-------------|--------|
| 1 | Project scaffolding & configuration | Complete |
| 2 | Pretix API client activity | Complete |
| 3 | Discord embed formatter activity | Complete |
| 4 | Discord webhook sender activity | Complete |
| 5 | Temporal workflow orchestration | Complete |
| 6 | FastAPI webhook endpoint | Complete |
| 7 | Worker entrypoint & end-to-end wiring | Complete |

## Implementation Guidelines

- **Language**: Python 3.13+ (match existing PyTexas toolchain)
- **Toolchain**: uv, ruff, mypy (strict), pytest, just
- **TDD**: Red-Green-Refactor for every step; run `just check` after each change
- **Type hints**: All functions, all parameters, all return types. No `Any`.
- **Absolute imports only**
- **Empty `__init__.py`** files
- **ABOUTME comments**: All code files start with a 2-line comment (first line prefixed `ABOUTME: `)
- **Temporal SDK**: `temporalio` Python package
- **HTTP**: `httpx` for async HTTP calls in activities
- **Web framework**: FastAPI with uvicorn

---

## Step 1: Project Scaffolding & Configuration

**Goal**: Set up the project structure, dependencies, tooling, and a configuration module with validation.

```text
Prompt for code-generation LLM:

1. RED: Write configuration validation tests first:
   - Create tests/test_config.py:
     - Test that load_config() reads all required env vars (PRETIX_API_TOKEN, DISCORD_WEBHOOK_URL) and returns a typed Settings dataclass
     - Test that load_config() raises a clear error when PRETIX_API_TOKEN is missing
     - Test that load_config() raises a clear error when DISCORD_WEBHOOK_URL is missing
     - Test that load_config() uses sensible defaults for optional vars (PRETIX_BASE_URL, TEMPORAL_ADDRESS, TEMPORAL_NAMESPACE, TEMPORAL_TASK_QUEUE)

2. Set up project scaffolding:
   - Create pyproject.toml with:
     - name = "pretix-discord"
     - requires-python = ">=3.13"
     - dependencies: temporalio, fastapi, uvicorn, httpx, pydantic-settings
     - dev dependencies: ruff, mypy, pytest, pytest-asyncio, nox, respx (httpx mock)
   - Create justfile with targets: default, check, fmt, test, all
   - Create src/pretix_discord/__init__.py (empty)
   - Create tests/__init__.py (empty)

3. GREEN: Write minimal code to make tests pass:
   - Create src/pretix_discord/config.py:
     - Define Settings dataclass with all config fields and defaults
     - Implement load_config() that reads from environment variables
     - Raise ValueError with descriptive message for missing required vars

4. REFACTOR: Ensure config module is clean and well-typed

5. Verify: run `just check` — ruff, mypy --strict, pytest must all pass
```

---

## Step 2: Pretix API Client Activity

**Goal**: Implement the `fetch_pretix_order` Temporal activity that calls the pretix REST API and returns typed order data.

```text
Prompt for code-generation LLM:

NOTE: Project scaffolding from Step 1 is in place. Settings dataclass exists in src/pretix_discord/config.py.

1. RED: Write tests for pretix order data parsing first:
   - Create tests/test_pretix.py:
     - Test that parse_pretix_order() extracts order code, email, total, and line items from a realistic pretix API response dict
     - Test that parse_pretix_order() handles orders with multiple line items (e.g., 2x Individual + 1x T-Shirt)
     - Test that parse_pretix_order() formats the total as a dollar string with 2 decimal places (pretix returns "99.00" as string)
     - Test that parse_pretix_order() raises ValueError for a response missing the "code" field

2. GREEN: Write minimal code to make tests pass:
   - Create src/pretix_discord/pretix.py:
     - Define PretixOrder dataclass with fields: code, email, total, event_name, line_items (list of strings like "1x Individual - In Person")
     - Implement parse_pretix_order(data: dict) -> PretixOrder

3. RED: Write tests for the fetch activity:
   - Add to tests/test_pretix.py:
     - Test that fetch_pretix_order activity calls the correct pretix API URL using respx to mock httpx
     - Test that fetch_pretix_order activity passes the Authorization header with the API token
     - Test that fetch_pretix_order activity raises on non-200 responses

4. GREEN: Implement the activity:
   - Add to src/pretix_discord/pretix.py:
     - Define FetchOrderInput dataclass with fields: organizer, event, code
     - Implement fetch_pretix_order(input: FetchOrderInput) -> PretixOrder as a Temporal activity
     - Use httpx.AsyncClient to GET the order, parse with parse_pretix_order()
     - Read PRETIX_API_TOKEN and PRETIX_BASE_URL from config

5. REFACTOR: Clean up, ensure types are tight

6. Verify: run `just check`
```

---

## Step 3: Discord Embed Formatter Activity

**Goal**: Implement the `format_discord_embed` activity that transforms a PretixOrder into a Discord webhook payload.

```text
Prompt for code-generation LLM:

NOTE: PretixOrder dataclass exists in src/pretix_discord/pretix.py from Step 2.

1. RED: Write tests for embed formatting first:
   - Create tests/test_discord.py:
     - Test that format_discord_embed() produces correct embed title: "{event_name}: A new order has been placed: {code}"
     - Test that format_discord_embed() includes "Order total" field with the dollar amount, inline=True
     - Test that format_discord_embed() includes "Email" field with buyer email, inline=True
     - Test that format_discord_embed() includes "Purchased products" field with newline-joined line items, inline=False
     - Test that format_discord_embed() sets username to "pretix" and footer text to "pretix"
     - Test that format_discord_embed() sets a green-ish color (3066993) for order.placed action
     - Test that format_discord_embed() with action "pretix.event.order.canceled" uses a red color (15158332)

2. GREEN: Write minimal code to make tests pass:
   - Create src/pretix_discord/discord.py:
     - Define DiscordEmbed, DiscordField, DiscordFooter, and DiscordPayload as dataclasses
     - Implement format_discord_embed(order: PretixOrder, action: str) -> DiscordPayload
     - Map action types to colors: placed=green, paid=blue, canceled=red, default=gray
     - Mark as Temporal activity

3. REFACTOR: Ensure the formatter is clean. Verify embed structure matches Discord's expected format.

4. Verify: run `just check`
```

---

## Step 4: Discord Webhook Sender Activity

**Goal**: Implement the `send_discord_webhook` activity that POSTs the formatted embed to Discord.

```text
Prompt for code-generation LLM:

NOTE: DiscordPayload dataclass exists in src/pretix_discord/discord.py from Step 3.

1. RED: Write tests for the Discord sender activity:
   - Create tests/test_discord_sender.py:
     - Test that send_discord_webhook() POSTs to the configured DISCORD_WEBHOOK_URL with correct JSON body using respx
     - Test that send_discord_webhook() sets Content-Type to application/json
     - Test that send_discord_webhook() raises on non-2xx responses from Discord
     - Test that send_discord_webhook() succeeds on 204 No Content (Discord's normal success response)

2. GREEN: Write minimal code to make tests pass:
   - Add to src/pretix_discord/discord.py:
     - Define SendWebhookInput dataclass wrapping the DiscordPayload
     - Implement send_discord_webhook(input: SendWebhookInput) -> None as a Temporal activity
     - Use httpx.AsyncClient to POST the JSON payload
     - Read DISCORD_WEBHOOK_URL from config

3. REFACTOR: Consider whether fetch and send should share an httpx client pattern

4. Verify: run `just check`
```

---

## Step 5: Temporal Workflow Orchestration

**Goal**: Implement the `PretixWebhookWorkflow` that chains the three activities together.

```text
Prompt for code-generation LLM:

NOTE: All three activities exist from Steps 2-4:
- fetch_pretix_order in src/pretix_discord/pretix.py
- format_discord_embed in src/pretix_discord/discord.py
- send_discord_webhook in src/pretix_discord/discord.py

1. RED: Write tests for the workflow:
   - Create tests/test_workflow.py:
     - Test that PretixWebhookWorkflow calls fetch_pretix_order with correct organizer/event/code from the webhook payload
     - Test that PretixWebhookWorkflow passes the fetched order and action to format_discord_embed
     - Test that PretixWebhookWorkflow passes the formatted payload to send_discord_webhook
     - Test that PretixWebhookWorkflow correctly extracts organizer, event, code, and action from the input
     - Use Temporal's testing framework (temporalio.testing.WorkflowEnvironment) with mocked activities

2. GREEN: Write minimal code to make tests pass:
   - Create src/pretix_discord/workflow.py:
     - Define WebhookInput dataclass with fields: organizer, event, code, action
     - Implement PretixWebhookWorkflow as a Temporal workflow class
     - In the run method: execute fetch_pretix_order -> format_discord_embed -> send_discord_webhook in sequence
     - Set appropriate activity timeouts (start_to_close: 30s) and retry policy (max 5 attempts, backoff)

3. REFACTOR: Ensure workflow is clean and idiomatic Temporal Python

4. Verify: run `just check`
```

---

## Step 6: FastAPI Webhook Endpoint

**Goal**: Implement the FastAPI app that receives pretix webhook POSTs and starts Temporal workflows.

```text
Prompt for code-generation LLM:

NOTE: PretixWebhookWorkflow and WebhookInput exist in src/pretix_discord/workflow.py from Step 5.

1. RED: Write tests for the webhook endpoint:
   - Create tests/test_api.py:
     - Test that POST /webhook with a valid pretix payload returns 200
     - Test that POST /webhook with missing "code" field returns 400
     - Test that POST /webhook with missing "action" field returns 400
     - Test that POST /webhook with missing "organizer" field returns 400
     - Test that the endpoint starts a Temporal workflow with the correct WebhookInput
     - Use FastAPI's TestClient and mock the Temporal client

2. GREEN: Write minimal code to make tests pass:
   - Create src/pretix_discord/api.py:
     - Define PretixWebhookPayload pydantic model for request validation
     - Create FastAPI app with POST /webhook endpoint
     - Endpoint validates payload, creates WebhookInput, starts PretixWebhookWorkflow via Temporal client
     - Use a workflow ID based on notification_id for idempotency
     - Return 200 on success (within pretix's expected 200-299 range)

3. RED: Add test for GET /health endpoint:
   - Test that GET /health returns 200 with {"status": "ok"}

4. GREEN: Add the health endpoint

5. REFACTOR: Clean up the API module

6. Verify: run `just check`
```

---

## Step 7: Worker Entrypoint & End-to-End Wiring

**Goal**: Create the Temporal worker entrypoint and wire everything together for deployment.

```text
Prompt for code-generation LLM:

NOTE: All components exist from Steps 1-6. This step wires them together.

1. Create the Temporal worker entrypoint:
   - Create src/pretix_discord/worker.py:
     - Register all three activities with the worker
     - Register PretixWebhookWorkflow
     - Connect to Temporal using config (address, namespace, task queue)
     - Run the worker with graceful shutdown

2. Create the web server entrypoint:
   - Create src/pretix_discord/main.py:
     - Initialize Temporal client
     - Attach it to the FastAPI app state
     - Run uvicorn

3. Create a Dockerfile (multi-stage):
   - Build stage: install dependencies with uv
   - Runtime stage: slim image with just the app
   - CMD runs both worker and web server (or document running separately)

4. Create docker-compose.yml for local development:
   - Services: temporal (dev server), worker, web
   - Environment variables via .env file
   - Create .env.example with all required vars documented

5. Update README or add usage notes:
   - How to run locally with docker-compose
   - How to configure pretix webhook to point at the endpoint
   - How to set up the Discord webhook URL

6. Run full verification: `just check`

7. Manual smoke test instructions:
   - Start docker-compose
   - curl -X POST http://localhost:8000/webhook with a sample pretix payload
   - Verify Discord message appears
```

---

## Success Metrics

- All tests pass with `just check` (ruff, mypy --strict, pytest)
- Sending a sample pretix webhook payload to the FastAPI endpoint results in a formatted Discord embed message
- The Discord message matches the style of the existing Slack notification (order code, total, email, products)
- Temporal provides retry/durability — if Discord is temporarily down, the message is delivered when it recovers
- Clean separation of concerns: each activity is independently testable
