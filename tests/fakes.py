"""In-memory адаптеры портов для тестов."""
from __future__ import annotations

import copy
import itertools
from dataclasses import replace

from salary.application.ports.repositories import (
    BonusRepository,
    SickLeaveRepository,
    UnitOfWork,
    UserRepository,
)
from salary.application.ports.security import PasswordHasher
from salary.domain.models import Bonus, SickLeave, SickLeaveStatus, User, UserStatus


class _Store:
    def __init__(self) -> None:
        self.users: dict[int, User] = {}
        self.bonuses: dict[int, Bonus] = {}
        self.leaves: dict[int, SickLeave] = {}
        self.ids = itertools.count(1)


class MemUserRepository(UserRepository):
    def __init__(self, store: _Store) -> None:
        self._st = store

    def add(self, user: User) -> User:
        user = replace(user, id=next(self._st.ids))
        self._st.users[user.id] = user
        return copy.copy(user)

    def update(self, user: User) -> User:
        self._st.users[user.id] = copy.copy(user)
        return copy.copy(user)

    def get(self, user_id: int) -> User | None:
        u = self._st.users.get(user_id)
        return copy.copy(u) if u else None

    def get_by_login(self, login: str) -> User | None:
        return next((copy.copy(u) for u in self._st.users.values() if u.login == login), None)

    def list(self, status: UserStatus | None = None) -> list[User]:
        return [copy.copy(u) for u in self._st.users.values() if status is None or u.status is status]


class MemBonusRepository(BonusRepository):
    def __init__(self, store: _Store) -> None:
        self._st = store

    def add(self, bonus: Bonus) -> Bonus:
        bonus = replace(bonus, id=next(self._st.ids))
        self._st.bonuses[bonus.id] = bonus
        return bonus

    def get(self, bonus_id: int) -> Bonus | None:
        return self._st.bonuses.get(bonus_id)

    def delete(self, bonus_id: int) -> None:
        self._st.bonuses.pop(bonus_id, None)

    def list_for_user(self, user_id: int, year: int | None = None, month: int | None = None) -> list[Bonus]:
        return [
            b
            for b in self._st.bonuses.values()
            if b.user_id == user_id and (year is None or b.year == year) and (month is None or b.month == month)
        ]


class MemSickLeaveRepository(SickLeaveRepository):
    def __init__(self, store: _Store) -> None:
        self._st = store

    def add(self, leave: SickLeave) -> SickLeave:
        leave = replace(leave, id=next(self._st.ids))
        self._st.leaves[leave.id] = leave
        return copy.copy(leave)

    def update(self, leave: SickLeave) -> SickLeave:
        self._st.leaves[leave.id] = copy.copy(leave)
        return copy.copy(leave)

    def get(self, leave_id: int) -> SickLeave | None:
        s = self._st.leaves.get(leave_id)
        return copy.copy(s) if s else None

    def list_for_user(self, user_id: int) -> list[SickLeave]:
        return [copy.copy(s) for s in self._st.leaves.values() if s.user_id == user_id]

    def list(self, status: SickLeaveStatus | None = None) -> list[SickLeave]:
        return [copy.copy(s) for s in self._st.leaves.values() if status is None or s.status is status]


class MemUnitOfWork(UnitOfWork):
    def __init__(self, store: _Store) -> None:
        self.users = MemUserRepository(store)
        self.bonuses = MemBonusRepository(store)
        self.sick_leaves = MemSickLeaveRepository(store)

    def commit(self) -> None:
        pass

    def rollback(self) -> None:
        pass


def make_uow_factory():
    store = _Store()
    return lambda: MemUnitOfWork(store)


class PlainHasher(PasswordHasher):
    def hash(self, password: str) -> str:
        return "h:" + password

    def verify(self, password: str, password_hash: str) -> bool:
        return password_hash == "h:" + password


class FakeEngine:
    def dispose(self) -> None:
        pass
