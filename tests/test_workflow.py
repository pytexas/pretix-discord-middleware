# ABOUTME: Tests for the PretixWebhookWorkflow Temporal workflow.
# Validates the workflow chain: fetch order -> format embed -> send webhook.

from __future__ import annotations

import uuid
from collections.abc import Callable
from typing import Any

import pytest
from temporalio import activity
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

from pretix_discord.discord_activities import format_discord_embed
from pretix_discord.models import (
    FetchOrderInput,
    PretixOrder,
    SendWebhookInput,
    WebhookInput,
)
from pretix_discord.workflow import PretixWebhookWorkflow

SAMPLE_ORDER = PretixOrder(
    code="T0AF2",
    email="buyer@example.com",
    total="$99.00",
    event_name="PyTexas 2025",
    line_items=["1x Individual - In Person"],
)

EXPECTED_PAYLOAD = format_discord_embed(SAMPLE_ORDER)


# Mock activities that record calls for verification
fetch_calls: list[FetchOrderInput] = []
send_calls: list[SendWebhookInput] = []


@activity.defn(name="fetch_pretix_order")
async def mock_fetch_pretix_order(inp: FetchOrderInput) -> PretixOrder:
    fetch_calls.append(inp)
    return SAMPLE_ORDER


@activity.defn(name="send_discord_webhook")
async def mock_send_discord_webhook(inp: SendWebhookInput) -> None:
    send_calls.append(inp)


@pytest.fixture(autouse=True)
def _clear_call_logs() -> None:
    fetch_calls.clear()
    send_calls.clear()


MOCK_ACTIVITIES: list[Callable[..., Any]] = [
    mock_fetch_pretix_order,
    mock_send_discord_webhook,
]


class TestPretixWebhookWorkflow:
    async def test_calls_fetch_with_correct_input(self) -> None:
        task_queue = str(uuid.uuid4())
        async with await WorkflowEnvironment.start_local() as env:
            async with Worker(
                env.client,
                task_queue=task_queue,
                workflows=[PretixWebhookWorkflow],
                activities=MOCK_ACTIVITIES,
            ):
                await env.client.execute_workflow(
                    PretixWebhookWorkflow.run,
                    WebhookInput(organizer="pytexas", event="2025", code="T0AF2"),
                    id=str(uuid.uuid4()),
                    task_queue=task_queue,
                )

        assert len(fetch_calls) == 1
        assert fetch_calls[0].organizer == "pytexas"
        assert fetch_calls[0].event == "2025"
        assert fetch_calls[0].code == "T0AF2"

    async def test_passes_formatted_payload_to_send(self) -> None:
        task_queue = str(uuid.uuid4())
        async with await WorkflowEnvironment.start_local() as env:
            async with Worker(
                env.client,
                task_queue=task_queue,
                workflows=[PretixWebhookWorkflow],
                activities=MOCK_ACTIVITIES,
            ):
                await env.client.execute_workflow(
                    PretixWebhookWorkflow.run,
                    WebhookInput(organizer="pytexas", event="2025", code="T0AF2"),
                    id=str(uuid.uuid4()),
                    task_queue=task_queue,
                )

        assert len(send_calls) == 1
        assert send_calls[0].payload == EXPECTED_PAYLOAD
