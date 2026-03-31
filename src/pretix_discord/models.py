# ABOUTME: Data models for the pretix-discord middleware.
# Contains all dataclasses used across activities and the workflow.

from __future__ import annotations

from dataclasses import dataclass
from typing import Any  # noqa: F401 - needed for raw JSON dict types


@dataclass(frozen=True)
class PretixOrder:
    """Parsed pretix order with display-ready fields."""

    code: str
    email: str
    total: str
    event_name: str
    line_items: list[str]


@dataclass(frozen=True)
class FetchOrderInput:
    """Input for the fetch_pretix_order activity."""

    organizer: str
    event: str
    code: str


@dataclass(frozen=True)
class DiscordField:
    """A single field in a Discord embed."""

    name: str
    value: str
    inline: bool = False


@dataclass(frozen=True)
class DiscordFooter:
    """Footer section of a Discord embed."""

    text: str


@dataclass(frozen=True)
class DiscordEmbed:
    """A Discord embed object."""

    title: str
    color: int
    fields: list[DiscordField]
    footer: DiscordFooter


@dataclass(frozen=True)
class DiscordPayload:
    """Complete Discord webhook payload."""

    username: str
    embeds: list[DiscordEmbed]

    def to_dict(self) -> dict[str, Any]:  # Any: raw JSON output
        """Convert to a dict matching Discord's webhook JSON format.

        Returns:
            Dictionary matching Discord's webhook embed JSON structure.
        """
        return {
            "username": self.username,
            "embeds": [
                {
                    "title": embed.title,
                    "color": embed.color,
                    "fields": [
                        {"name": f.name, "value": f.value, "inline": f.inline}
                        for f in embed.fields
                    ],
                    "footer": {"text": embed.footer.text},
                }
                for embed in self.embeds
            ],
        }


@dataclass(frozen=True)
class SendWebhookInput:
    """Input for the send_discord_webhook activity."""

    payload: DiscordPayload
    order_code: str


@dataclass(frozen=True)
class WebhookInput:
    """Input for the PretixWebhookWorkflow."""

    organizer: str
    event: str
    code: str
