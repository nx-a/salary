"""Входящий HTTP-адаптер: FastAPI-приложение."""
from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from salary.adapters.inbound.http.routers import admin, auth, me
from salary.adapters.outbound.persistence.database import create_schema
from salary.config import Settings, get_settings
from salary.container import Container
from salary.domain.errors import (
    AccessDeniedError,
    AlreadyExistsError,
    AuthenticationError,
    DomainError,
    NotFoundError,
    ValidationError,
)

_ERROR_STATUS: dict[type[DomainError], int] = {
    AuthenticationError: status.HTTP_401_UNAUTHORIZED,
    AccessDeniedError: status.HTTP_403_FORBIDDEN,
    NotFoundError: status.HTTP_404_NOT_FOUND,
    AlreadyExistsError: status.HTTP_409_CONFLICT,
    ValidationError: status.HTTP_422_UNPROCESSABLE_CONTENT,
}


def create_app(settings: Settings | None = None, container: Container | None = None) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.container = container or Container.build(settings)
        if container is None:
            create_schema(app.state.container.engine)
        app.state.container.auth.ensure_admin(settings.admin_login, settings.admin_password)
        yield
        app.state.container.engine.dispose()

    app = FastAPI(title="Учёт заработной платы", version="0.1.0", lifespan=lifespan)

    @app.exception_handler(DomainError)
    async def domain_error_handler(_: Request, exc: DomainError) -> JSONResponse:
        code = next((c for t, c in _ERROR_STATUS.items() if isinstance(exc, t)), status.HTTP_400_BAD_REQUEST)
        headers = {"WWW-Authenticate": "Bearer"} if code == status.HTTP_401_UNAUTHORIZED else None
        return JSONResponse({"detail": str(exc)}, status_code=code, headers=headers)

    for router in (auth.router, me.router, admin.router):
        app.include_router(router, prefix="/api")

    # Статика монтируется последней, чтобы не перехватывать /api.
    app.mount("/", StaticFiles(directory=settings.static_dir, html=True), name="static")
    return app
