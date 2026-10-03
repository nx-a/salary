"""Расчёт заработной платы за месяц. Чистая логика без ввода-вывода.

Правила:
* дневная ставка = оклад / число рабочих дней (пн–пт) в месяце;
* за каждый рабочий день подтверждённого больничного оплачивается 50 % дневной ставки;
* к начислению прибавляются премии и надбавки за этот месяц;
* больничный, захватывающий несколько месяцев, учитывается только в пределах расчётного месяца;
* округление до копеек по правилу half-up.
"""
from __future__ import annotations

import calendar
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

from salary.domain.models import Bonus, BonusKind, SickLeave, SickLeaveStatus, User

SICK_PAY_RATE = Decimal("0.5")
_KOPECK = Decimal("0.01")


def _money(value: Decimal) -> Decimal:
    return value.quantize(_KOPECK, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class Payslip:
    user_id: int
    year: int
    month: int
    base_salary: Decimal
    working_days: int
    sick_days: int
    daily_rate: Decimal
    worked_pay: Decimal
    sick_pay: Decimal
    bonuses_total: Decimal
    allowances_total: Decimal
    total: Decimal


class PayrollCalculator:
    """Доменный сервис расчёта начислений."""

    def __init__(self, sick_pay_rate: Decimal = SICK_PAY_RATE) -> None:
        self._sick_pay_rate = sick_pay_rate

    @staticmethod
    def month_bounds(year: int, month: int) -> tuple[date, date]:
        last = calendar.monthrange(year, month)[1]
        return date(year, month, 1), date(year, month, last)

    @staticmethod
    def working_days(start: date, end: date) -> int:
        days, current = 0, start
        while current <= end:
            if current.weekday() < 5:
                days += 1
            current += timedelta(days=1)
        return days

    def sick_working_days(self, leaves: Iterable[SickLeave], year: int, month: int) -> int:
        first, last = self.month_bounds(year, month)
        total = 0
        for leave in leaves:
            if leave.status is not SickLeaveStatus.APPROVED:
                continue
            start, end = max(leave.date_from, first), min(leave.date_to, last)
            if start <= end:
                total += self.working_days(start, end)
        return total

    def calculate(
        self,
        user: User,
        year: int,
        month: int,
        bonuses: Iterable[Bonus],
        sick_leaves: Iterable[SickLeave],
    ) -> Payslip:
        first, last = self.month_bounds(year, month)
        working_days = self.working_days(first, last)
        sick_days = min(self.sick_working_days(sick_leaves, year, month), working_days)

        daily_rate = user.base_salary / working_days if working_days else Decimal(0)
        worked_pay = daily_rate * (working_days - sick_days)
        sick_pay = daily_rate * sick_days * self._sick_pay_rate

        month_bonuses = [b for b in bonuses if b.year == year and b.month == month]
        bonuses_total = sum((b.amount for b in month_bonuses if b.kind is BonusKind.BONUS), Decimal(0))
        allowances_total = sum((b.amount for b in month_bonuses if b.kind is BonusKind.ALLOWANCE), Decimal(0))

        worked_pay, sick_pay = _money(worked_pay), _money(sick_pay)
        return Payslip(
            user_id=user.id or 0,
            year=year,
            month=month,
            base_salary=_money(user.base_salary),
            working_days=working_days,
            sick_days=sick_days,
            daily_rate=_money(daily_rate),
            worked_pay=worked_pay,
            sick_pay=sick_pay,
            bonuses_total=_money(bonuses_total),
            allowances_total=_money(allowances_total),
            total=worked_pay + sick_pay + _money(bonuses_total) + _money(allowances_total),
        )
