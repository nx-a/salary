from datetime import date, timedelta
from decimal import Decimal

import pytest
from fakes import PlainHasher, make_uow_factory

from salary.adapters.outbound.security.jwt_tokens import JwtTokenService
from salary.application.services.auth import AuthService
from salary.application.services.employees import EmployeeService
from salary.application.services.payroll import PayrollService
from salary.application.services.sick_leaves import SickLeaveService
from salary.domain.errors import AccessDeniedError, AlreadyExistsError, AuthenticationError, ValidationError
from salary.domain.models import BonusKind, Role, SickLeaveStatus
from salary.domain.payroll import PayrollCalculator


@pytest.fixture
def services():
    uow = make_uow_factory()
    auth = AuthService(uow, PlainHasher(), JwtTokenService("test-secret-" + "x" * 32, timedelta(minutes=5)))
    return auth, EmployeeService(uow), SickLeaveService(uow), PayrollService(uow, PayrollCalculator())


def test_registration_requires_admin_verification(services):
    auth, employees, *_ = services
    user = auth.register("ivan", "secret1", "Иван Иванов")
    with pytest.raises(AccessDeniedError):
        auth.login("ivan", "secret1")
    employees.verify(user.id)
    token, logged = auth.login("ivan", "secret1")
    assert logged.role is Role.USER
    assert auth.authenticate(token).id == user.id


def test_login_errors(services):
    auth, *_ = services
    auth.register("ivan", "secret1", "Иван")
    with pytest.raises(AuthenticationError):
        auth.login("ivan", "wrong")
    with pytest.raises(AlreadyExistsError):
        auth.register("ivan", "secret1", "Иван")


def test_rejected_user_loses_access_with_existing_token(services):
    auth, employees, *_ = services
    user = auth.register("ivan", "secret1", "Иван")
    employees.verify(user.id)
    token, _ = auth.login("ivan", "secret1")
    employees.reject(user.id)
    with pytest.raises(AccessDeniedError):
        auth.authenticate(token)


def test_ensure_admin_is_idempotent(services):
    auth, *_ = services
    first = auth.ensure_admin("admin", "admin123")
    second = auth.ensure_admin("admin", "admin123")
    assert first.id == second.id and first.is_admin


def test_sick_leave_overlap_and_payslip(services):
    auth, employees, sick, payroll = services
    user = auth.register("ivan", "secret1", "Иван")
    employees.verify(user.id)
    employees.set_salary(user.id, Decimal("22000"))
    employees.add_bonus(user.id, Decimal("3000"), BonusKind.BONUS, 2026, 10, "за проект")

    leave = sick.create(user.id, date(2026, 10, 5), date(2026, 10, 9))
    with pytest.raises(ValidationError):
        sick.create(user.id, date(2026, 10, 9), date(2026, 10, 12))

    # До подтверждения больничный не влияет на расчёт.
    assert payroll.payslip(user.id, 2026, 10).total == Decimal("25000.00")

    approved = sick.approve(leave.id)
    assert approved.status is SickLeaveStatus.APPROVED
    with pytest.raises(ValidationError):
        sick.reject(leave.id)
    assert payroll.payslip(user.id, 2026, 10).total == Decimal("22500.00")


def test_rejected_sick_leave_frees_dates(services):
    auth, employees, sick, _ = services
    user = auth.register("ivan", "secret1", "Иван")
    leave = sick.create(user.id, date(2026, 10, 5), date(2026, 10, 9))
    sick.reject(leave.id)
    assert sick.create(user.id, date(2026, 10, 5), date(2026, 10, 9)).id


def test_negative_salary_rejected(services):
    auth, employees, *_ = services
    user = auth.register("ivan", "secret1", "Иван")
    with pytest.raises(ValidationError):
        employees.set_salary(user.id, Decimal("-1"))
