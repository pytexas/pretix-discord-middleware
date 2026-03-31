# ABOUTME: Pretix API client activities.
# Provides order parsing and a Temporal activity to fetch orders from pretix.

from __future__ import annotations

from collections import Counter
from typing import Any  # noqa: F401 - needed for raw JSON dict types

import httpx
from temporalio import activity

from pretix_discord.config import load_config
from pretix_discord.models import FetchOrderInput, PretixOrder


def parse_pretix_order(
    data: dict[str, Any],  # Any: raw JSON input
    item_names: dict[int, str],
    variation_names: dict[int, str],
) -> PretixOrder:
    """Parse a pretix API order response dict into a PretixOrder.

    Args:
        data: Raw JSON dict from the pretix order API endpoint.
        item_names: Mapping of item ID to display name.
        variation_names: Mapping of variation ID to display name.

    Returns:
        Parsed order with display-ready fields.

    Raises:
        ValueError: If the response is missing the ``code`` field.
    """
    if "code" not in data:
        raise ValueError("Missing required field: code")

    event_data = data.get("event", "Unknown Event")
    if isinstance(event_data, dict):
        event_name_data = event_data.get("name", {})
        event_name = (
            event_name_data.get("en", "Unknown Event")
            if isinstance(event_name_data, dict)
            else str(event_name_data)
        )
    else:
        event_name = str(event_data)

    raw_total = data["total"]
    total = f"${raw_total}"

    positions = data.get("positions", [])
    item_counts: Counter[str] = Counter()
    for pos in positions:
        item_id = pos.get("item")
        variation_id = pos.get("variation")
        name = item_names.get(item_id, "Unknown Item") if item_id is not None else "Unknown Item"
        if variation_id is not None:
            variation = variation_names.get(variation_id)
            if variation:
                name = f"{name} - {variation}"
        item_counts[name] += 1

    line_items = [f"{count}x {name}" for name, count in item_counts.items()]

    return PretixOrder(
        code=data["code"],
        email=data["email"],
        total=total,
        event_name=event_name,
        line_items=line_items,
    )


def _build_item_lookups(
    items_data: list[dict[str, Any]],  # Any: raw JSON input
) -> tuple[dict[int, str], dict[int, str]]:
    """Build item and variation name lookup dicts from a pretix items API response.

    Args:
        items_data: List of item dicts from the pretix items API endpoint.

    Returns:
        Tuple of (item_names, variation_names) dicts mapping IDs to display names.
    """
    item_names: dict[int, str] = {}
    variation_names: dict[int, str] = {}

    for item in items_data:
        item_id = item["id"]
        name_data = item.get("name", {})
        item_names[item_id] = (
            name_data.get("en", str(item_id))
            if isinstance(name_data, dict)
            else str(name_data)
        )
        for variation in item.get("variations", []):
            var_id = variation["id"]
            var_name_data = variation.get("value", {})
            variation_names[var_id] = (
                var_name_data.get("en", str(var_id))
                if isinstance(var_name_data, dict)
                else str(var_name_data)
            )

    return item_names, variation_names


@activity.defn
async def fetch_pretix_order(inp: FetchOrderInput) -> PretixOrder:
    """Fetch an order from the pretix API and return parsed order data.

    Fetches both the order and the event's item catalog to resolve item names.

    Args:
        inp: Organizer, event, and order code identifying the order.

    Returns:
        Parsed order with display-ready fields.

    Raises:
        httpx.HTTPStatusError: If the pretix API returns a non-200 response.
    """
    config = load_config()
    base = f"{config.pretix_base_url}/organizers/{inp.organizer}/events/{inp.event}"
    headers = {"Authorization": f"Token {config.pretix_api_token}"}

    activity.logger.info("Fetching order %s from pretix", inp.code)

    async with httpx.AsyncClient() as client:
        order_response, items_response = await _fetch_order_and_items(
            client, base, inp.code, headers
        )

    item_names, variation_names = _build_item_lookups(items_response.get("results", []))
    activity.logger.info("Successfully fetched order %s", inp.code)
    return parse_pretix_order(order_response, item_names, variation_names)


async def _fetch_order_and_items(
    client: httpx.AsyncClient,
    base_url: str,
    order_code: str,
    headers: dict[str, str],
) -> tuple[dict[str, Any], dict[str, Any]]:  # Any: raw JSON output
    """Concurrently fetch the order and items list from the pretix API.

    Args:
        client: Shared httpx async client.
        base_url: Base URL for the organizer/event (without trailing slash).
        order_code: The pretix order code.
        headers: Authorization headers to include in both requests.

    Returns:
        Tuple of (order_data, items_data) as raw JSON dicts.

    Raises:
        httpx.HTTPStatusError: If either API call returns a non-200 response.
    """
    import asyncio

    order_req = client.get(f"{base_url}/orders/{order_code}/", headers=headers)
    items_req = client.get(f"{base_url}/items/", headers=headers)

    order_response, items_response = await asyncio.gather(order_req, items_req)
    order_response.raise_for_status()
    items_response.raise_for_status()

    return order_response.json(), items_response.json()
