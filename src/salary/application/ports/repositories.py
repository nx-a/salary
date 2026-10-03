"""Исходящие порты хранения данных."""
from __future__ import annotations

from abc import ABC, abstractmethod
from types import TracebackType
from typing import Self

from salary.domain.models import Bonus, SickLeave, SickLeaveStatus, User, UserStatus


class UserRepository(ABC):
    @abstractmethod
    def add(self, user: User) -> User: ...

    @abstractmethod
    def update(self, user: User) -> User: ...

    @abstractmethod
    def get(self, user_id: int) -> User | None: ...

    @abstractmethod
    def get_by_login(self, login: str) -> User | None: ...

    @abstractmethod
    def list(self, status: UserStatus | None = None) -> list[User]: ...


class BonusRepository(ABC):
    @abstractmethod
    def add(self, bonus: Bonus) -> Bonus: ...

    @abstractmethod
    def get(self, bonus_id: int) -> Bonus | None: ...

    @abstractmethod
    def delete(self, bonus_id: int) -> None: ...

    @abstractmethod
    def list_for_user(self, user_id: int, year: int | None = None, month: int | None = None) -> list[Bonus]: ...


class SickLeaveRepository(ABC):
    @abstractmethod
    def add(self, leave: SickLeave) -> SickLeave: ...

    @abstractmethod
    def update(self, leave: SickLeave) -> SickLeave: ...

    @abstractmethod
    def get(self, leave_id: int) -> SickLeave | None: ...

    @abstractmethod
    def list_for_user(self, user_id: int) -> list[SickLeave]: ...

    @abstractmethod
    def list(self, status: SickLeaveStatus | None = None) -> list[SickLeave]: ...


class UnitOfWork(ABC):
    """Транзакция над всеми репозиториями."""

    users: UserRepository
    bonuses: BonusRepository
    sick_leaves: SickLeaveRepository

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if exc_type is None:
            self.commit()
        else:
            self.rollback()

    @abstractmethod
    def commit(self) -> None: ...

    @abstractmethod
    def rollback(self) -> None: ...
