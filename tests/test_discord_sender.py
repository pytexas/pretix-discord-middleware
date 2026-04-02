# ABOUTME: Tests for the Discord webhook sender activity.
# Validates that send_discord_webhook() POSTs correctly to Discord.

from __future__ import annotations

import os
from unittest.mock import patch

import httpx
import pytest
import respx

from pretix_discord.discord_activities import send_discord_webhook
from pretix_discord.models import (
    DiscordEmbed,
    DiscordField,
    DiscordFooter,
    DiscordPayload,
    SendWebhookInput,
)

WEBHOOK_URL = "https://discord.com/api/webhooks/123/abc-token"

ENV = {
    "PRETIX_API_TOKEN": "test-token",
    "DISCORD_WEBHOOK_URL": WEBHOOK_URL,
}


def _make_payload() -> DiscordPayload:
    return DiscordPayload(
        username="pretix",
        embeds=[
            DiscordEmbed(
                title="PyTexas 2025: A new order has been placed: T0AF2",
                color=3066993,
                fields=[
                    DiscordField(name="Order total", value="$99.00", inline=True),
                    DiscordField(name="Email", value="buyer@example.com", inline=True),
                    DiscordField(
                        name="Purchased products",
                        value="1x Individual - In Person",
                        inline=False,
                    ),
                ],
                footer=DiscordFooter(text="pretix"),
            )
        ],
    )


class TestSendDiscordWebhook:
    @respx.mock
    async def test_posts_to_webhook_url_with_correct_body(self) -> None:
        payload = _make_payload()
        route = respx.post(WEBHOOK_URL).mock(
            return_value=httpx.Response(204),
        )

        with patch.dict(os.environ, ENV, clear=True):
            await send_discord_webhook(SendWebhookInput(payload=payload, order_code="T0AF2"))

        assert route.called
        request = route.calls[0].request
        assert request.url == WEBHOOK_URL
        # Verify the JSON body contains our embed data
        import json

        body = json.loads(request.content)
        assert body["username"] == "pretix"
        assert body["embeds"][0]["title"] == "PyTexas 2025: A new order has been placed: T0AF2"

    @respx.mock
    async def test_sets_content_type_json(self) -> None:
        payload = _make_payload()
        route = respx.post(WEBHOOK_URL).mock(
            return_value=httpx.Response(204),
        )

        with patch.dict(os.environ, ENV, clear=True):
            await send_discord_webhook(SendWebhookInput(payload=payload, order_code="T0AF2"))

        request = route.calls[0].request
        assert "application/json" in request.headers["content-type"]

    @respx.mock
    async def test_raises_on_non_2xx_response(self) -> None:
        payload = _make_payload()
        respx.post(WEBHOOK_URL).mock(
            return_value=httpx.Response(429, json={"message": "rate limited"}),
        )

        with patch.dict(os.environ, ENV, clear=True):
            with pytest.raises(httpx.HTTPStatusError):
                await send_discord_webhook(SendWebhookInput(payload=payload, order_code="T0AF2"))

    @respx.mock
    async def test_succeeds_on_204_no_content(self) -> None:
        payload = _make_payload()
        respx.post(WEBHOOK_URL).mock(
            return_value=httpx.Response(204),
        )

        with patch.dict(os.environ, ENV, clear=True):
            # Should not raise
            await send_discord_webhook(SendWebhookInput(payload=payload, order_code="T0AF2"))
