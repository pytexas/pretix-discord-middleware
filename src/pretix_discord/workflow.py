# ABOUTME: Temporal workflow that orchestrates the pretix-to-Discord pipeline.
# Chains fetch_pretix_order -> format_discord_embed -> send_discord_webhook.

from __future__ import annotations

from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from pretix_discord.discord_activities import (
        format_discord_embed,
        send_discord_webhook,
    )
    from pretix_discord.models import FetchOrderInput, SendWebhookInput, WebhookInput
    from pretix_discord.pretix_activities import fetch_pretix_order


@workflow.defn
class PretixWebhookWorkflow:
    """Workflow that fetches a pretix order and sends a Discord notification."""

    @workflow.run
    async def run(self, inp: WebhookInput) -> None:
        order = await workflow.execute_activity(
            fetch_pretix_order,
            FetchOrderInput(
                organizer=inp.organizer,
                event=inp.event,
                code=inp.code,
            ),
            start_to_close_timeout=timedelta(seconds=30),
        )

        payload = format_discord_embed(order)

        await workflow.execute_activity(
            send_discord_webhook,
            SendWebhookInput(payload=payload),
            start_to_close_timeout=timedelta(seconds=30),
        )
