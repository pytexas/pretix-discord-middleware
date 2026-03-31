# ABOUTME: Temporal worker entrypoint.
# Registers workflows and activities, connects to Temporal, and runs the worker.

from __future__ import annotations

import asyncio

from temporalio.client import Client
from temporalio.worker import Worker

from pretix_discord.config import load_config
from pretix_discord.discord_activities import send_discord_webhook
from pretix_discord.pretix_activities import fetch_pretix_order
from pretix_discord.workflow import PretixWebhookWorkflow


async def main() -> None:
    """Connect to Temporal and run the worker until interrupted.

    Raises:
        ValueError: If required configuration is missing.
    """
    config = load_config()

    client = await Client.connect(
        config.temporal_address,
        namespace=config.temporal_namespace,
    )

    worker = Worker(
        client,
        task_queue=config.temporal_task_queue,
        workflows=[PretixWebhookWorkflow],
        activities=[
            fetch_pretix_order,
            send_discord_webhook,
        ],
    )
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
