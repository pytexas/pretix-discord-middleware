# ABOUTME: Tests for the FastAPI webhook endpoint.
# Validates request handling, payload validation, and Temporal workflow dispatch.

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from pretix_discord.api import app
from pretix_discord.models import WebhookInput


def _valid_payload() -> dict[str, str | int]:
    return {
        "notification_id": 12345,
        "organizer": "pytexas",
        "event": "2025",
        "code": "T0AF2",
        "action": "pretix.event.order.placed",
    }


@pytest.fixture()
def mock_temporal_client() -> AsyncMock:
    mock_client = AsyncMock()
    mock_client.start_workflow = AsyncMock(return_value=MagicMock(id="wf-123"))
    return mock_client


@pytest.fixture()
def client(mock_temporal_client: AsyncMock) -> TestClient:
    app.state.temporal_client = mock_temporal_client
    return TestClient(app)


class TestPostWebhook:
    def test_valid_payload_returns_200(self, client: TestClient) -> None:
        response = client.post("/webhook", json=_valid_payload())
        assert response.status_code == 200

    def test_missing_code_returns_422(self, client: TestClient) -> None:
        payload = _valid_payload()
        del payload["code"]
        response = client.post("/webhook", json=payload)
        assert response.status_code == 422

    def test_missing_organizer_returns_422(self, client: TestClient) -> None:
        payload = _valid_payload()
        del payload["organizer"]
        response = client.post("/webhook", json=payload)
        assert response.status_code == 422

    def test_missing_event_returns_422(self, client: TestClient) -> None:
        payload = _valid_payload()
        del payload["event"]
        response = client.post("/webhook", json=payload)
        assert response.status_code == 422

    def test_starts_workflow_with_correct_input(
        self, client: TestClient, mock_temporal_client: AsyncMock
    ) -> None:
        client.post("/webhook", json=_valid_payload())

        mock_temporal_client.start_workflow.assert_called_once()
        call_args = mock_temporal_client.start_workflow.call_args
        # First positional arg is the workflow run method, second is the input
        webhook_input = call_args.args[1]
        assert isinstance(webhook_input, WebhookInput)
        assert webhook_input.organizer == "pytexas"
        assert webhook_input.event == "2025"
        assert webhook_input.code == "T0AF2"

    def test_workflow_id_uses_notification_id(
        self, client: TestClient, mock_temporal_client: AsyncMock
    ) -> None:
        client.post("/webhook", json=_valid_payload())

        call_kwargs = mock_temporal_client.start_workflow.call_args.kwargs
        assert "12345" in call_kwargs["id"]


class TestGetHealth:
    def test_returns_200_with_status_ok(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
