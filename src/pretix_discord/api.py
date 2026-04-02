# ABOUTME: FastAPI application with webhook and health endpoints.
# Receives pretix webhook POSTs and dispatches Temporal workflows.

from __future__ import annotations

from fastapi import FastAPI, Request
from pydantic import BaseModel

from pretix_discord.models import WebhookInput
from pretix_discord.workflow import PretixWebhookWorkflow

app = FastAPI(title="pretix-discord")


class PretixWebhookPayload(BaseModel):
    """Pydantic model for incoming pretix webhook requests."""

    notification_id: int
    organizer: str
    event: str
    code: str
    action: str


@app.post("/webhook")
async def handle_webhook(payload: PretixWebhookPayload, request: Request) -> dict[str, str]:
    """Receive a pretix webhook and start a Temporal workflow.

    Args:
        payload: Validated pretix webhook payload.
        request: FastAPI request object for accessing app state.

    Returns:
        Acknowledgement with the started workflow ID.
    """
    client = request.app.state.temporal_client
    inp = WebhookInput(
        organizer=payload.organizer,
        event=payload.event,
        code=payload.code,
    )
    workflow_id = f"pretix-order-{payload.notification_id}"

    await client.start_workflow(
        PretixWebhookWorkflow.run,
        inp,
        id=workflow_id,
        task_queue="pretix-discord",
    )

    return {"status": "ok", "workflow_id": workflow_id}


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint.

    Returns:
        Simple status dict.
    """
    return {"status": "ok"}
