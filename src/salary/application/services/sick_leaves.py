"""Сценарии учёта больничных."""
from __future__ import annotations

from collections.abc import Callable
from datetime import date

from salary.application.ports.repositories import UnitOfWork
from salary.domain.errors import NotFoundError, ValidationError
from salary.domain.models import SickLeave, SickLeaveStatus


class SickLeaveService:
    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    def create(self, user_id: int, date_from: date, date_to: date, comment: str = "") -> SickLeave:
        """Сотрудник заводит больничный; он учитывается после подтверждения администратором."""
        leave = SickLeave(user_id=user_id, date_from=date_from, date_to=date_to, comment=comment.strip())
        with self._uow_factory() as uow:
            for existing in uow.sick_leaves.list_for_user(user_id):
                if existing.is_active and existing.overlaps(leave):
                    raise ValidationError(
                        f"Пересечение с больничным {existing.date_from:%d.%m.%Y}–{existing.date_to:%d.%m.%Y}"
                    )
            return uow.sick_leaves.add(leave)

    def list_for_user(self, user_id: int) -> list[SickLeave]:
        with self._uow_factory() as uow:
            return uow.sick_leaves.list_for_user(user_id)

    def list(self, status: SickLeaveStatus | None = None) -> list[SickLeave]:
        with self._uow_factory() as uow:
            return uow.sick_leaves.list(status)

    def approve(self, leave_id: int) -> SickLeave:
        with self._uow_factory() as uow:
            leave = self._get(uow, leave_id)
            leave.approve()
            return uow.sick_leaves.update(leave)

    def reject(self, leave_id: int) -> SickLeave:
        with self._uow_factory() as uow:
            leave = self._get(uow, leave_id)
            leave.reject()
            return uow.sick_leaves.update(leave)

    @staticmethod
    def _get(uow: UnitOfWork, leave_id: int) -> SickLeave:
        leave = uow.sick_leaves.get(leave_id)
        if leave is None:
            raise NotFoundError("Больничный не найден")
        return leave
