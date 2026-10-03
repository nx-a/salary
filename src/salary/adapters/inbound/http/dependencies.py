from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from salary.container import Container
from salary.domain.errors import AccessDeniedError, AuthenticationError
from salary.domain.models import User

_bearer = HTTPBearer(auto_error=False)


def get_container(request: Request) -> Container:
    return request.app.state.container


ContainerDep = Annotated[Container, Depends(get_container)]


def get_current_user(
    container: ContainerDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> User:
    if credentials is None:
        raise AuthenticationError("Требуется авторизация")
    return container.auth.authenticate(credentials.credentials)


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_admin(user: CurrentUser) -> User:
    if not user.is_admin:
        raise AccessDeniedError("Требуются права администратора")
    return user


AdminUser = Annotated[User, Depends(require_admin)]
