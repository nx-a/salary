"""Сценарии регистрации и аутентификации."""
from __future__ import annotations

from collections.abc import Callable

from salary.application.ports.repositories import UnitOfWork
from salary.application.ports.security import PasswordHasher, TokenClaims, TokenService
from salary.domain.errors import AccessDeniedError, AlreadyExistsError, AuthenticationError, ValidationError
from salary.domain.models import Role, User, UserStatus

MIN_PASSWORD_LENGTH = 6


class AuthService:
    def __init__(
        self,
        uow_factory: Callable[[], UnitOfWork],
        hasher: PasswordHasher,
        tokens: TokenService,
    ) -> None:
        self._uow_factory = uow_factory
        self._hasher = hasher
        self._tokens = tokens

    def register(self, login: str, password: str, full_name: str) -> User:
        """Регистрирует сотрудника. Вход возможен после подтверждения администратором."""
        return self._create(login, password, full_name, Role.USER, UserStatus.PENDING)

    def ensure_admin(self, login: str, password: str) -> User:
        """Создаёт администратора, если пользователя с таким логином ещё нет."""
        with self._uow_factory() as uow:
            existing = uow.users.get_by_login(login)
        if existing:
            return existing
        return self._create(login, password, "Администратор", Role.ADMIN, UserStatus.ACTIVE)

    def login(self, login: str, password: str) -> tuple[str, User]:
        with self._uow_factory() as uow:
            user = uow.users.get_by_login(login.strip())
        if user is None or not self._hasher.verify(password, user.password_hash):
            raise AuthenticationError("Неверный логин или пароль")
        if user.status is UserStatus.PENDING:
            raise AccessDeniedError("Учётная запись ожидает подтверждения администратором")
        if user.status is UserStatus.REJECTED:
            raise AccessDeniedError("Учётная запись отклонена администратором")
        return self._tokens.issue(TokenClaims(user_id=user.id, role=user.role)), user

    def authenticate(self, token: str) -> User:
        """Возвращает актуального пользователя по токену (с перечиткой из БД)."""
        claims = self._tokens.decode(token)
        with self._uow_factory() as uow:
            user = uow.users.get(claims.user_id)
        if user is None:
            raise AuthenticationError("Пользователь не найден")
        if not user.is_active:
            raise AccessDeniedError("Учётная запись не активна")
        return user

    def _create(self, login: str, password: str, full_name: str, role: Role, status: UserStatus) -> User:
        login, full_name = login.strip(), full_name.strip()
        if not login:
            raise ValidationError("Логин обязателен")
        if not full_name:
            raise ValidationError("ФИО обязательно")
        if len(password) < MIN_PASSWORD_LENGTH:
            raise ValidationError(f"Пароль должен быть не короче {MIN_PASSWORD_LENGTH} символов")
        with self._uow_factory() as uow:
            if uow.users.get_by_login(login):
                raise AlreadyExistsError("Пользователь с таким логином уже существует")
            return uow.users.add(
                User(
                    login=login,
                    password_hash=self._hasher.hash(password),
                    full_name=full_name,
                    role=role,
                    status=status,
                )
            )
