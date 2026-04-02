# ABOUTME: Tests for the configuration module.
# Validates that load_config() reads env vars correctly and raises on missing required vars.

import os
from unittest.mock import patch

import pytest

from pretix_discord.config import Settings, load_config


class TestLoadConfig:
    def test_loads_required_env_vars(self) -> None:
        env = {
            "PRETIX_API_TOKEN": "test-token-123",
            "DISCORD_WEBHOOK_URL": "https://discord.com/api/webhooks/123/abc",
        }
        with patch.dict(os.environ, env, clear=True):
            settings = load_config()

        assert isinstance(settings, Settings)
        assert settings.pretix_api_token == "test-token-123"
        assert settings.discord_webhook_url == "https://discord.com/api/webhooks/123/abc"

    def test_raises_when_pretix_api_token_missing(self) -> None:
        env = {
            "DISCORD_WEBHOOK_URL": "https://discord.com/api/webhooks/123/abc",
        }
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValueError, match="PRETIX_API_TOKEN"):
                load_config()

    def test_raises_when_discord_webhook_url_missing(self) -> None:
        env = {
            "PRETIX_API_TOKEN": "test-token-123",
        }
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValueError, match="DISCORD_WEBHOOK_URL"):
                load_config()

    def test_uses_sensible_defaults_for_optional_vars(self) -> None:
        env = {
            "PRETIX_API_TOKEN": "test-token-123",
            "DISCORD_WEBHOOK_URL": "https://discord.com/api/webhooks/123/abc",
        }
        with patch.dict(os.environ, env, clear=True):
            settings = load_config()

        assert settings.pretix_base_url == "https://pretix.eu/api/v1"
        assert settings.temporal_address == "localhost:7233"
        assert settings.temporal_namespace == "default"
        assert settings.temporal_task_queue == "pretix-discord"

    def test_overrides_optional_vars_from_env(self) -> None:
        env = {
            "PRETIX_API_TOKEN": "test-token-123",
            "DISCORD_WEBHOOK_URL": "https://discord.com/api/webhooks/123/abc",
            "PRETIX_BASE_URL": "https://custom.pretix.eu/api/v1",
            "TEMPORAL_ADDRESS": "temporal.example.com:7233",
            "TEMPORAL_NAMESPACE": "production",
            "TEMPORAL_TASK_QUEUE": "custom-queue",
        }
        with patch.dict(os.environ, env, clear=True):
            settings = load_config()

        assert settings.pretix_base_url == "https://custom.pretix.eu/api/v1"
        assert settings.temporal_address == "temporal.example.com:7233"
        assert settings.temporal_namespace == "production"
        assert settings.temporal_task_queue == "custom-queue"
