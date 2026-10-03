"""Точка входа ASGI: `uvicorn salary.main:app`."""
from salary.adapters.inbound.http.app import create_app

app = create_app()
