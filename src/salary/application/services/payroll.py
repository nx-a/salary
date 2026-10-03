"""Сценарий расчёта зарплаты."""
from __future__ import annotations

from collections.abc import Callable

from salary.application.ports.repositories import UnitOfWork
from salary.domain.errors import NotFoundError
from salary.domain.payroll import PayrollCalculator, Payslip


class PayrollService:
    def __init__(self, uow_factory: Callable[[], UnitOfWork], calculator: PayrollCalculator) -> None:
        self._uow_factory = uow_factory
        self._calculator = calculator

    def payslip(self, user_id: int, year: int, month: int) -> Payslip:
        with self._uow_factory() as uow:
            user = uow.users.get(user_id)
            if user is None:
                raise NotFoundError("Сотрудник не найден")
            bonuses = uow.bonuses.list_for_user(user_id, year, month)
            leaves = uow.sick_leaves.list_for_user(user_id)
        return self._calculator.calculate(user, year, month, bonuses, leaves)
