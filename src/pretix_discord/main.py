# ABOUTME: FastAPI web server entrypoint.
# Initializes the Temporal client, attaches it to the app, and runs uvicorn.

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import uvicorn
from temporalio.client import Client

from pretix_discord.api import app
from pretix_discord.config import load_config


@asynccontextmanager
async def lifespan(app_instance: object) -> AsyncIterator[None]:
    """Initialize and tear down the Temporal client with the app lifecycle.

    Args:
        app_instance: The FastAPI application instance.

    Yields:
        None after the Temporal client is attached to app state.
    """
    config = load_config()
    client = await Client.connect(
        config.temporal_address,
        namespace=config.temporal_namespace,
    )
    app.state.temporal_client = client
    yield


app.router.lifespan_context = lifespan


def main() -> None:
    """Entry point for running the FastAPI web server."""
    uvicorn.run(
        "pretix_discord.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )


if __name__ == "__main__":
    main()
