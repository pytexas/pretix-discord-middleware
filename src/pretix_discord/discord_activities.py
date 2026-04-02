# ABOUTME: Discord webhook activities.
# Formats pretix orders into Discord embeds and sends them via webhook.

from __future__ import annotations

import httpx
from temporalio import activity

from pretix_discord.config import load_config
from pretix_discord.models import (
    DiscordEmbed,
    DiscordField,
    DiscordFooter,
    DiscordPayload,
    PretixOrder,
    SendWebhookInput,
)

EMBED_COLOR = 3066993  # green


def format_discord_embed(order: PretixOrder) -> DiscordPayload:
    """Format a PretixOrder into a Discord webhook payload.

    Args:
        order: Parsed pretix order to format.

    Returns:
        Discord webhook payload ready to be sent.
    """
    fields = [
        DiscordField(name="Order total", value=order.total, inline=True),
        DiscordField(name="Email", value=order.email, inline=True),
        DiscordField(
            name="Purchased products",
            value="\n".join(order.line_items),
            inline=False,
        ),
    ]

    embed = DiscordEmbed(
        title=f"{order.event_name}: A new order has been placed: {order.code}",
        color=EMBED_COLOR,
        fields=fields,
        footer=DiscordFooter(text="pretix"),
    )

    return DiscordPayload(username="pretix", embeds=[embed])


@activity.defn
async def send_discord_webhook(inp: SendWebhookInput) -> None:
    """POST a Discord webhook payload to the configured webhook URL.

    Args:
        inp: Wrapper containing the Discord payload to send.

    Raises:
        httpx.HTTPStatusError: If Discord returns a non-2xx response.
    """
    config = load_config()
    activity.logger.info("Sending Discord webhook for order %s", inp.order_code)

    async with httpx.AsyncClient() as client:
        response = await client.post(
            config.discord_webhook_url,
            json=inp.payload.to_dict(),
        )
        response.raise_for_status()

    activity.logger.info(
        "Discord webhook sent successfully for order %s (HTTP %s)",
        inp.order_code,
        response.status_code,
    )
