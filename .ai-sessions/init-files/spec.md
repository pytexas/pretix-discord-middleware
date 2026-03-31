# Pretix-to-Discord Webhook Middleware

## Problem

PyTexas uses pretix (SaaS) for ticket sales. Pretix supports webhooks that fire on events like
`pretix.event.order.placed`, but it sends a minimal JSON payload:

```json
{
  "notification_id": 123455,
  "organizer": "pytexas",
  "event": "2026",
  "code": "ABC23",
  "action": "pretix.event.order.placed"
}
```

Discord webhooks expect a different format (`{"content": "..."}` or embeds). Sending pretix
webhooks directly to Discord fails with a 400 because Discord doesn't recognize pretix's fields.

The team currently receives rich Slack notifications (via pretix's built-in Slack integration)
showing order code, total, buyer email, and purchased products. They want the same experience
in Discord.

## Solution

A lightweight middleware service that:

1. Receives pretix webhook POST requests
2. Fetches full order details from the pretix REST API
3. Formats the data as a Discord embed (rich message)
4. Posts the embed to a configured Discord webhook URL

Built as a **Temporal application** for durability — if the pretix API or Discord is temporarily
unavailable, Temporal retries automatically without losing the webhook event.

## Architecture

```
pretix (SaaS) --webhook POST--> FastAPI endpoint --starts--> Temporal Workflow
                                                                  |
                                                          Activities:
                                                          1. Fetch order from pretix API
                                                          2. Format Discord embed
                                                          3. Post to Discord webhook
```

### Components

- **FastAPI web server**: Receives pretix webhook POSTs, starts a Temporal workflow for each
- **Temporal Workflow** (`PretixWebhookWorkflow`): Orchestrates the three activities in sequence
- **Activities**:
  - `fetch_pretix_order`: GET `/api/v1/organizers/{org}/events/{event}/orders/{code}/` with API token auth
  - `format_discord_embed`: Transforms pretix order data into a Discord embed payload
  - `send_discord_webhook`: POSTs the embed to the Discord webhook URL

### Discord Embed Format (target output)

Mirroring the Slack notification style:

```json
{
  "username": "pretix",
  "embeds": [{
    "title": "PyTexas 2026: A new order has been placed: ABC23",
    "color": 3066993,
    "fields": [
      {"name": "Order total", "value": "$99.00", "inline": true},
      {"name": "Email", "value": "buyer@example.com", "inline": true},
      {"name": "Purchased products", "value": "1x Individual - In Person", "inline": false}
    ],
    "footer": {"text": "pretix"}
  }]
}
```

## Configuration

Environment variables:

- `PRETIX_API_TOKEN`: API token for pretix REST API
- `PRETIX_BASE_URL`: Base URL for pretix API (default: `https://pretix.eu/api/v1`)
- `DISCORD_WEBHOOK_URL`: Discord webhook endpoint
- `TEMPORAL_ADDRESS`: Temporal server address (default: `localhost:7233`)
- `TEMPORAL_NAMESPACE`: Temporal namespace (default: `default`)
- `TEMPORAL_TASK_QUEUE`: Task queue name (default: `pretix-discord`)

## Supported Webhook Actions

Initially support `pretix.event.order.placed`. Design the formatter so additional action types
(e.g., `order.paid`, `order.canceled`, `checkin`) can be added later without restructuring.

## Non-Goals

- No persistent database — Temporal provides durability
- No authentication on the webhook endpoint (pretix doesn't sign webhooks on SaaS) — rely on
  URL obscurity and network controls
- No Discord bot — only webhook integration
- No UI or admin panel
