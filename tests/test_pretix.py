# ABOUTME: Tests for the pretix API client module.
# Covers order parsing logic and the fetch_pretix_order Temporal activity.

from __future__ import annotations

import os
from unittest.mock import patch

import httpx
import pytest
import respx

from pretix_discord.models import FetchOrderInput, PretixOrder
from pretix_discord.pretix_activities import fetch_pretix_order, parse_pretix_order


def _make_order_response(
    *,
    code: str = "T0AF2",
    email: str = "buyer@example.com",
    total: str = "99.00",
    event_name: str = "PyTexas 2025",
    positions: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    """Build a realistic pretix order API response dict."""
    if positions is None:
        positions = [
            {
                "id": 1,
                "item": 100,
                "variation": None,
                "price": "99.00",
                "attendee_name": "Test User",
                "item_name": "Individual - In Person",
                "variation_name": None,
            },
        ]
    return {
        "code": code,
        "email": email,
        "total": total,
        "event": {"name": {"en": event_name}, "slug": "pytexas-2025"},
        "positions": positions,
    }


class TestParsePretixOrder:
    def test_extracts_order_fields(self) -> None:
        data = _make_order_response()
        order = parse_pretix_order(data)

        assert isinstance(order, PretixOrder)
        assert order.code == "T0AF2"
        assert order.email == "buyer@example.com"
        assert order.total == "$99.00"
        assert order.event_name == "PyTexas 2025"
        assert order.line_items == ["1x Individual - In Person"]

    def test_handles_multiple_line_items(self) -> None:
        positions: list[dict[str, object]] = [
            {
                "id": 1,
                "item": 100,
                "variation": None,
                "price": "99.00",
                "item_name": "Individual - In Person",
                "variation_name": None,
            },
            {
                "id": 2,
                "item": 100,
                "variation": None,
                "price": "99.00",
                "item_name": "Individual - In Person",
                "variation_name": None,
            },
            {
                "id": 3,
                "item": 200,
                "variation": 10,
                "price": "25.00",
                "item_name": "T-Shirt",
                "variation_name": "Large",
            },
        ]
        data = _make_order_response(total="223.00", positions=positions)
        order = parse_pretix_order(data)

        assert "2x Individual - In Person" in order.line_items
        assert "1x T-Shirt - Large" in order.line_items

    def test_formats_total_as_dollar_string(self) -> None:
        data = _make_order_response(total="99.00")
        order = parse_pretix_order(data)
        assert order.total == "$99.00"

        data2 = _make_order_response(total="0.00")
        order2 = parse_pretix_order(data2)
        assert order2.total == "$0.00"

    def test_raises_on_missing_code(self) -> None:
        data = _make_order_response()
        del data["code"]

        with pytest.raises(ValueError, match="code"):
            parse_pretix_order(data)


class TestFetchPretixOrder:
    @respx.mock
    async def test_calls_correct_api_url(self) -> None:
        env = {
            "PRETIX_API_TOKEN": "token-abc",
            "DISCORD_WEBHOOK_URL": "https://discord.com/api/webhooks/1/x",
            "PRETIX_BASE_URL": "https://pretix.eu/api/v1",
        }
        order_data = _make_order_response()
        route = respx.get(
            "https://pretix.eu/api/v1/organizers/pytexas/events/2025/orders/T0AF2/"
        ).mock(return_value=httpx.Response(200, json=order_data))

        with patch.dict(os.environ, env, clear=True):
            inp = FetchOrderInput(organizer="pytexas", event="2025", code="T0AF2")
            order = await fetch_pretix_order(inp)

        assert route.called
        assert order.code == "T0AF2"

    @respx.mock
    async def test_passes_authorization_header(self) -> None:
        env = {
            "PRETIX_API_TOKEN": "token-secret",
            "DISCORD_WEBHOOK_URL": "https://discord.com/api/webhooks/1/x",
            "PRETIX_BASE_URL": "https://pretix.eu/api/v1",
        }
        order_data = _make_order_response()
        route = respx.get(
            "https://pretix.eu/api/v1/organizers/pytexas/events/2025/orders/T0AF2/"
        ).mock(return_value=httpx.Response(200, json=order_data))

        with patch.dict(os.environ, env, clear=True):
            inp = FetchOrderInput(organizer="pytexas", event="2025", code="T0AF2")
            await fetch_pretix_order(inp)

        assert route.calls[0].request.headers["Authorization"] == "Token token-secret"

    @respx.mock
    async def test_raises_on_non_200_response(self) -> None:
        env = {
            "PRETIX_API_TOKEN": "token-abc",
            "DISCORD_WEBHOOK_URL": "https://discord.com/api/webhooks/1/x",
            "PRETIX_BASE_URL": "https://pretix.eu/api/v1",
        }
        respx.get("https://pretix.eu/api/v1/organizers/pytexas/events/2025/orders/NOPE/").mock(
            return_value=httpx.Response(404, json={"detail": "Not found."})
        )

        with patch.dict(os.environ, env, clear=True):
            inp = FetchOrderInput(organizer="pytexas", event="2025", code="NOPE")
            with pytest.raises(httpx.HTTPStatusError):
                await fetch_pretix_order(inp)
