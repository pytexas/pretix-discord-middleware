# ABOUTME: Pretix API client activities.
# Provides order parsing and a Temporal activity to fetch orders from pretix.

from __future__ import annotations

from collections import Counter
from typing import Any  # noqa: F401 - needed for raw JSON dict types

import httpx
from temporalio import activity

from pretix_discord.config import load_config
from pretix_discord.models import FetchOrderInput, PretixOrder


def parse_pretix_order(data: dict[str, Any]) -> PretixOrder:  # Any: raw JSON input
    """Parse a pretix API order response dict into a PretixOrder.

    Args:
        data: Raw JSON dict from the pretix order API endpoint.

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
        name = pos.get("item_name", "Unknown Item")
        variation = pos.get("variation_name")
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


@activity.defn
async def fetch_pretix_order(inp: FetchOrderInput) -> PretixOrder:
    """Fetch an order from the pretix API and return parsed order data.

    Args:
        inp: Organizer, event, and order code identifying the order.

    Returns:
        Parsed order with display-ready fields.

    Raises:
        httpx.HTTPStatusError: If the pretix API returns a non-200 response.
    """
    config = load_config()
    url = (
        f"{config.pretix_base_url}/organizers/{inp.organizer}"
        f"/events/{inp.event}/orders/{inp.code}/"
    )

    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            headers={"Authorization": f"Token {config.pretix_api_token}"},
        )
        response.raise_for_status()

    return parse_pretix_order(response.json())
