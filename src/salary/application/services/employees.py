"""Сценарии управления сотрудниками, окладами, премиями и надбавками."""
from __future__ import annotations

from collections.abc import Callable
from decimal import Decimal

from salary.application.ports.repositories import UnitOfWork
from salary.domain.errors import NotFoundError
from salary.domain.models import Bonus, BonusKind, User, UserStatus


class EmployeeService:
    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    def get(self, user_id: int) -> User:
        with self._uow_factory() as uow:
            return self._get(uow, user_id)

    def list(self, status: UserStatus | None = None) -> list[User]:
        with self._uow_factory() as uow:
            return uow.users.list(status)

    def verify(self, user_id: int) -> User:
        with self._uow_factory() as uow:
            user = self._get(uow, user_id)
            user.verify()
            return uow.users.update(user)

    def reject(self, user_id: int) -> User:
        with self._uow_factory() as uow:
            user = self._get(uow, user_id)
            user.reject()
            return uow.users.update(user)

    def set_salary(self, user_id: int, amount: Decimal) -> User:
        with self._uow_factory() as uow:
            user = self._get(uow, user_id)
            user.set_base_salary(amount)
            return uow.users.update(user)

    def add_bonus(
        self, user_id: int, amount: Decimal, kind: BonusKind, year: int, month: int, comment: str = ""
    ) -> Bonus:
        with self._uow_factory() as uow:
            self._get(uow, user_id)
            bonus = Bonus(user_id=user_id, amount=amount, kind=kind, year=year, month=month, comment=comment.strip())
            return uow.bonuses.add(bonus)

    def delete_bonus(self, bonus_id: int) -> None:
        with self._uow_factory() as uow:
            if uow.bonuses.get(bonus_id) is None:
                raise NotFoundError("Премия не найдена")
            uow.bonuses.delete(bonus_id)

    def bonuses(self, user_id: int, year: int | None = None, month: int | None = None) -> list[Bonus]:
        with self._uow_factory() as uow:
            self._get(uow, user_id)
            return uow.bonuses.list_for_user(user_id, year, month)

    @staticmethod
    def _get(uow: UnitOfWork, user_id: int) -> User:
        user = uow.users.get(user_id)
        if user is None:
            raise NotFoundError("Сотрудник не найден")
        return user
