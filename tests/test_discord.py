# ABOUTME: Tests for the Discord embed formatter activity.
# Validates that format_discord_embed() produces correct Discord webhook payloads.

from __future__ import annotations

from pretix_discord.discord_activities import format_discord_embed
from pretix_discord.models import DiscordPayload, PretixOrder


def _make_order(
    *,
    code: str = "T0AF2",
    email: str = "buyer@example.com",
    total: str = "$99.00",
    event_name: str = "PyTexas 2025",
    line_items: list[str] | None = None,
) -> PretixOrder:
    return PretixOrder(
        code=code,
        email=email,
        total=total,
        event_name=event_name,
        line_items=line_items or ["1x Individual - In Person"],
    )


class TestFormatDiscordEmbed:
    def test_embed_title(self) -> None:
        order = _make_order()
        payload = format_discord_embed(order)

        assert isinstance(payload, DiscordPayload)
        embed = payload.embeds[0]
        assert embed.title == "PyTexas 2025: A new order has been placed: T0AF2"

    def test_order_total_field(self) -> None:
        order = _make_order(total="$149.00")
        payload = format_discord_embed(order)

        embed = payload.embeds[0]
        total_fields = [f for f in embed.fields if f.name == "Order total"]
        assert len(total_fields) == 1
        assert total_fields[0].value == "$149.00"
        assert total_fields[0].inline is True

    def test_email_field(self) -> None:
        order = _make_order(email="test@pytexas.org")
        payload = format_discord_embed(order)

        embed = payload.embeds[0]
        email_fields = [f for f in embed.fields if f.name == "Email"]
        assert len(email_fields) == 1
        assert email_fields[0].value == "test@pytexas.org"
        assert email_fields[0].inline is True

    def test_purchased_products_field(self) -> None:
        order = _make_order(line_items=["2x Individual - In Person", "1x T-Shirt - Large"])
        payload = format_discord_embed(order)

        embed = payload.embeds[0]
        products_fields = [f for f in embed.fields if f.name == "Purchased products"]
        assert len(products_fields) == 1
        assert products_fields[0].value == "2x Individual - In Person\n1x T-Shirt - Large"
        assert products_fields[0].inline is False

    def test_username_and_footer(self) -> None:
        order = _make_order()
        payload = format_discord_embed(order)

        assert payload.username == "pretix"
        embed = payload.embeds[0]
        assert embed.footer.text == "pretix"

    def test_green_color_for_placed_action(self) -> None:
        order = _make_order()
        payload = format_discord_embed(order)

        assert payload.embeds[0].color == 3066993
