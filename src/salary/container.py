"""Composition root: связывает порты с адаптерами."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from functools import partial

from sqlalchemy import Engine

from salary.adapters.outbound.persistence.database import make_engine, make_session_factory
from salary.adapters.outbound.persistence.repositories import SqlUnitOfWork
from salary.adapters.outbound.security.bcrypt_hasher import BcryptPasswordHasher
from salary.adapters.outbound.security.jwt_tokens import JwtTokenService
from salary.application.services.auth import AuthService
from salary.application.services.employees import EmployeeService
from salary.application.services.payroll import PayrollService
from salary.application.services.sick_leaves import SickLeaveService
from salary.config import Settings
from salary.domain.payroll import PayrollCalculator


@dataclass
class Container:
    engine: Engine
    auth: AuthService
    employees: EmployeeService
    sick_leaves: SickLeaveService
    payroll: PayrollService

    @classmethod
    def build(cls, settings: Settings) -> Container:
        engine = make_engine(settings.database_url)
        uow_factory = partial(SqlUnitOfWork, make_session_factory(engine))
        tokens = JwtTokenService(settings.jwt_secret, timedelta(minutes=settings.jwt_ttl_minutes))
        return cls(
            engine=engine,
            auth=AuthService(uow_factory, BcryptPasswordHasher(), tokens),
            employees=EmployeeService(uow_factory),
            sick_leaves=SickLeaveService(uow_factory),
            payroll=PayrollService(uow_factory, PayrollCalculator()),
        )
