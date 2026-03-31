# ABOUTME: Tests for the pretix API client module.
# Covers order parsing logic and the fetch_pretix_order Temporal activity.

from __future__ import annotations

import os
from unittest.mock import patch

import httpx
import pytest
import respx

from pretix_discord.models import FetchOrderInput, PretixOrder
from pretix_discord.pretix_activities import (
    _build_item_lookups,
    fetch_pretix_order,
    parse_pretix_order,
)


def _make_order_response(
    *,
    code: str = "T0AF2",
    email: str = "buyer@example.com",
    total: str = "99.00",
    event: str = "pytexas-2025",
    positions: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    """Build a realistic pretix order API response dict.

    Matches the real pretix API shape: item/variation are IDs, not names.
    """
    if positions is None:
        positions = [
            {
                "id": 1,
                "item": 100,
                "variation": None,
                "price": "99.00",
                "attendee_name": "Test User",
            },
        ]
    return {
        "code": code,
        "email": email,
        "total": total,
        "event": event,
        "positions": positions,
    }


def _make_items_response(
    items: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    """Build a pretix items API response dict."""
    if items is None:
        items = [
            {
                "id": 100,
                "name": {"en": "Individual - In Person"},
                "variations": [],
            },
        ]
    return {"count": len(items), "results": items}


class TestBuildItemLookups:
    def test_builds_item_name_lookup(self) -> None:
        items = [{"id": 100, "name": {"en": "Individual - In Person"}, "variations": []}]
        item_names, _ = _build_item_lookups(items)
        assert item_names[100] == "Individual - In Person"

    def test_builds_variation_name_lookup(self) -> None:
        items = [
            {
                "id": 200,
                "name": {"en": "T-Shirt"},
                "variations": [
                    {"id": 10, "value": {"en": "Large"}},
                    {"id": 11, "value": {"en": "Medium"}},
                ],
            }
        ]
        _, variation_names = _build_item_lookups(items)
        assert variation_names[10] == "Large"
        assert variation_names[11] == "Medium"

    def test_handles_empty_items(self) -> None:
        item_names, variation_names = _build_item_lookups([])
        assert item_names == {}
        assert variation_names == {}


class TestParsePretixOrder:
    def test_extracts_order_fields(self) -> None:
        data = _make_order_response()
        item_names = {100: "Individual - In Person"}
        order = parse_pretix_order(data, item_names, {})

        assert isinstance(order, PretixOrder)
        assert order.code == "T0AF2"
        assert order.email == "buyer@example.com"
        assert order.total == "$99.00"
        assert order.event_name == "pytexas-2025"
        assert order.line_items == ["1x Individual - In Person"]

    def test_handles_multiple_line_items(self) -> None:
        positions: list[dict[str, object]] = [
            {"id": 1, "item": 100, "variation": None, "price": "99.00"},
            {"id": 2, "item": 100, "variation": None, "price": "99.00"},
            {"id": 3, "item": 200, "variation": 10, "price": "25.00"},
        ]
        data = _make_order_response(total="223.00", positions=positions)
        item_names = {100: "Individual - In Person", 200: "T-Shirt"}
        variation_names = {10: "Large"}
        order = parse_pretix_order(data, item_names, variation_names)

        assert "2x Individual - In Person" in order.line_items
        assert "1x T-Shirt - Large" in order.line_items

    def test_falls_back_to_unknown_item_when_id_not_in_lookup(self) -> None:
        data = _make_order_response()
        order = parse_pretix_order(data, {}, {})
        assert order.line_items == ["1x Unknown Item"]

    def test_formats_total_as_dollar_string(self) -> None:
        data = _make_order_response(total="99.00")
        order = parse_pretix_order(data, {100: "Ticket"}, {})
        assert order.total == "$99.00"

        data2 = _make_order_response(total="0.00")
        order2 = parse_pretix_order(data2, {100: "Ticket"}, {})
        assert order2.total == "$0.00"

    def test_raises_on_missing_code(self) -> None:
        data = _make_order_response()
        del data["code"]

        with pytest.raises(ValueError, match="code"):
            parse_pretix_order(data, {}, {})


class TestFetchPretixOrder:
    @respx.mock
    async def test_calls_correct_api_urls(self) -> None:
        env = {
            "PRETIX_API_TOKEN": "token-abc",
            "DISCORD_WEBHOOK_URL": "https://discord.com/api/webhooks/1/x",
            "PRETIX_BASE_URL": "https://pretix.eu/api/v1",
        }
        order_route = respx.get(
            "https://pretix.eu/api/v1/organizers/pytexas/events/2025/orders/T0AF2/"
        ).mock(return_value=httpx.Response(200, json=_make_order_response()))
        items_route = respx.get(
            "https://pretix.eu/api/v1/organizers/pytexas/events/2025/items/"
        ).mock(return_value=httpx.Response(200, json=_make_items_response()))

        with patch.dict(os.environ, env, clear=True):
            inp = FetchOrderInput(organizer="pytexas", event="2025", code="T0AF2")
            order = await fetch_pretix_order(inp)

        assert order_route.called
        assert items_route.called
        assert order.code == "T0AF2"

    @respx.mock
    async def test_passes_authorization_header(self) -> None:
        env = {
            "PRETIX_API_TOKEN": "token-secret",
            "DISCORD_WEBHOOK_URL": "https://discord.com/api/webhooks/1/x",
            "PRETIX_BASE_URL": "https://pretix.eu/api/v1",
        }
        order_route = respx.get(
            "https://pretix.eu/api/v1/organizers/pytexas/events/2025/orders/T0AF2/"
        ).mock(return_value=httpx.Response(200, json=_make_order_response()))
        respx.get(
            "https://pretix.eu/api/v1/organizers/pytexas/events/2025/items/"
        ).mock(return_value=httpx.Response(200, json=_make_items_response()))

        with patch.dict(os.environ, env, clear=True):
            inp = FetchOrderInput(organizer="pytexas", event="2025", code="T0AF2")
            await fetch_pretix_order(inp)

        assert order_route.calls[0].request.headers["Authorization"] == "Token token-secret"

    @respx.mock
    async def test_raises_on_non_200_response(self) -> None:
        env = {
            "PRETIX_API_TOKEN": "token-abc",
            "DISCORD_WEBHOOK_URL": "https://discord.com/api/webhooks/1/x",
            "PRETIX_BASE_URL": "https://pretix.eu/api/v1",
        }
        respx.get(
            "https://pretix.eu/api/v1/organizers/pytexas/events/2025/orders/NOPE/"
        ).mock(return_value=httpx.Response(404, json={"detail": "Not found."}))
        respx.get(
            "https://pretix.eu/api/v1/organizers/pytexas/events/2025/items/"
        ).mock(return_value=httpx.Response(200, json=_make_items_response()))

        with patch.dict(os.environ, env, clear=True):
            inp = FetchOrderInput(organizer="pytexas", event="2025", code="NOPE")
            with pytest.raises(httpx.HTTPStatusError):
                await fetch_pretix_order(inp)

    @respx.mock
    async def test_resolves_item_names_from_items_endpoint(self) -> None:
        env = {
            "PRETIX_API_TOKEN": "token-abc",
            "DISCORD_WEBHOOK_URL": "https://discord.com/api/webhooks/1/x",
            "PRETIX_BASE_URL": "https://pretix.eu/api/v1",
        }
        positions = [{"id": 1, "item": 100, "variation": None, "price": "99.00"}]
        respx.get(
            "https://pretix.eu/api/v1/organizers/pytexas/events/2025/orders/T0AF2/"
        ).mock(return_value=httpx.Response(200, json=_make_order_response(positions=positions)))
        respx.get(
            "https://pretix.eu/api/v1/organizers/pytexas/events/2025/items/"
        ).mock(return_value=httpx.Response(200, json=_make_items_response()))

        with patch.dict(os.environ, env, clear=True):
            inp = FetchOrderInput(organizer="pytexas", event="2025", code="T0AF2")
            order = await fetch_pretix_order(inp)

        assert order.line_items == ["1x Individual - In Person"]
