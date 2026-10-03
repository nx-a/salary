"""Исходящие порты безопасности."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from salary.domain.models import Role


class PasswordHasher(ABC):
    @abstractmethod
    def hash(self, password: str) -> str: ...

    @abstractmethod
    def verify(self, password: str, password_hash: str) -> bool: ...


@dataclass(frozen=True)
class TokenClaims:
    user_id: int
    role: Role


class TokenService(ABC):
    @abstractmethod
    def issue(self, claims: TokenClaims) -> str: ...

    @abstractmethod
    def decode(self, token: str) -> TokenClaims:
        """Разбирает токен; при ошибке бросает AuthenticationError."""
