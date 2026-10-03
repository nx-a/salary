from __future__ import annotations

from fastapi import APIRouter, status

from salary.adapters.inbound.http.dependencies import ContainerDep, CurrentUser
from salary.adapters.inbound.http.schemas import LoginIn, RegisterIn, TokenOut, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(body: RegisterIn, container: ContainerDep):
    return container.auth.register(body.login, body.password, body.full_name)


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, container: ContainerDep):
    token, user = container.auth.login(body.login, body.password)
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser):
    return user
