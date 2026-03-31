# ABOUTME: Configuration module for the pretix-discord middleware.
# Loads and validates settings from environment variables.

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Application settings loaded from environment variables."""

    pretix_api_token: str
    discord_webhook_url: str
    pretix_base_url: str = "https://pretix.eu/api/v1"
    temporal_address: str = "localhost:7233"
    temporal_namespace: str = "default"
    temporal_task_queue: str = "pretix-discord"


def load_config() -> Settings:
    """Load configuration from environment variables.

    Returns:
        Validated settings with all required and optional values populated.

    Raises:
        ValueError: If ``PRETIX_API_TOKEN`` or ``DISCORD_WEBHOOK_URL`` is missing.
    """
    pretix_api_token = os.environ.get("PRETIX_API_TOKEN")
    if not pretix_api_token:
        raise ValueError("PRETIX_API_TOKEN environment variable is required")

    discord_webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not discord_webhook_url:
        raise ValueError("DISCORD_WEBHOOK_URL environment variable is required")

    return Settings(
        pretix_api_token=pretix_api_token,
        discord_webhook_url=discord_webhook_url,
        pretix_base_url=os.environ.get("PRETIX_BASE_URL", "https://pretix.eu/api/v1"),
        temporal_address=os.environ.get("TEMPORAL_ADDRESS", "localhost:7233"),
        temporal_namespace=os.environ.get("TEMPORAL_NAMESPACE", "default"),
        temporal_task_queue=os.environ.get("TEMPORAL_TASK_QUEUE", "pretix-discord"),
    )
