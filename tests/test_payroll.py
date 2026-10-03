from datetime import date
from decimal import Decimal

import pytest

from salary.domain.errors import ValidationError
from salary.domain.models import Bonus, BonusKind, SickLeave, SickLeaveStatus, User
from salary.domain.payroll import PayrollCalculator

calc = PayrollCalculator()


def employee(salary: str = "100000") -> User:
    return User(id=1, login="ivan", password_hash="x", full_name="Иван", base_salary=Decimal(salary))


def approved(date_from: date, date_to: date) -> SickLeave:
    return SickLeave(user_id=1, date_from=date_from, date_to=date_to, status=SickLeaveStatus.APPROVED)


def test_working_days_in_october_2026():
    first, last = calc.month_bounds(2026, 10)
    assert calc.working_days(first, last) == 22


def test_full_month_without_sick_leave_equals_salary_plus_bonuses():
    bonuses = [
        Bonus(user_id=1, amount=Decimal("5000"), kind=BonusKind.BONUS, year=2026, month=10),
        Bonus(user_id=1, amount=Decimal("2500.50"), kind=BonusKind.ALLOWANCE, year=2026, month=10),
        Bonus(user_id=1, amount=Decimal("9999"), kind=BonusKind.BONUS, year=2026, month=9),
    ]
    slip = calc.calculate(employee(), 2026, 10, bonuses, [])
    assert slip.sick_days == 0
    assert slip.worked_pay == Decimal("100000.00")
    assert slip.bonuses_total == Decimal("5000.00")
    assert slip.allowances_total == Decimal("2500.50")
    assert slip.total == Decimal("107500.50")


def test_sick_days_paid_at_half_rate():
    # Октябрь 2026: 22 рабочих дня, ставка 1000/день. Больничный пн 5 — пт 9 = 5 рабочих дней.
    slip = calc.calculate(employee("22000"), 2026, 10, [], [approved(date(2026, 10, 5), date(2026, 10, 9))])
    assert slip.daily_rate == Decimal("1000.00")
    assert slip.sick_days == 5
    assert slip.worked_pay == Decimal("17000.00")
    assert slip.sick_pay == Decimal("2500.00")
    assert slip.total == Decimal("19500.00")


def test_cross_month_sick_leave_is_clipped():
    # 28.09.2026 (пн) — 02.10.2026 (пт): 3 дня в сентябре, 2 дня в октябре.
    leave = approved(date(2026, 9, 28), date(2026, 10, 2))
    assert calc.calculate(employee(), 2026, 9, [], [leave]).sick_days == 3
    assert calc.calculate(employee(), 2026, 10, [], [leave]).sick_days == 2


def test_weekends_not_counted_and_pending_ignored():
    weekend = approved(date(2026, 10, 3), date(2026, 10, 4))
    pending = SickLeave(user_id=1, date_from=date(2026, 10, 12), date_to=date(2026, 10, 16))
    assert calc.calculate(employee(), 2026, 10, [], [weekend, pending]).sick_days == 0


def test_rounding_half_up():
    # 100000 / 22 = 4545.4545... → 4545.45
    slip = calc.calculate(employee(), 2026, 10, [], [approved(date(2026, 10, 1), date(2026, 10, 1))])
    assert slip.daily_rate == Decimal("4545.45")
    assert slip.sick_pay == Decimal("2272.73")
    assert slip.total == slip.worked_pay + slip.sick_pay


def test_invalid_sick_leave_dates():
    with pytest.raises(ValidationError):
        SickLeave(user_id=1, date_from=date(2026, 10, 5), date_to=date(2026, 10, 1))
