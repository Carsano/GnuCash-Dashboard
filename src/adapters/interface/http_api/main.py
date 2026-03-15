"""Uvicorn entrypoint for local HTTP API development."""

from src.adapters.interface.http_api.app import create_app

app = create_app()

