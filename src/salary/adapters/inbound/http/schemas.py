"""DTO REST API."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from salary.domain.models import BonusKind, Role, SickLeaveStatus, UserStatus


class _Out(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class RegisterIn(BaseModel):
    login: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=6, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)


class LoginIn(BaseModel):
    login: str
    password: str


class UserOut(_Out):
    id: int
    login: str
    full_name: str
    role: Role
    status: UserStatus
    base_salary: Decimal
    created_at: datetime


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class SalaryIn(BaseModel):
    base_salary: Decimal = Field(ge=0, max_digits=12, decimal_places=2)


class BonusIn(BaseModel):
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    kind: BonusKind
    year: int = Field(ge=2000, le=2100)
    month: int = Field(ge=1, le=12)
    comment: str = Field(default="", max_length=1000)


class BonusOut(_Out):
    id: int
    user_id: int
    amount: Decimal
    kind: BonusKind
    year: int
    month: int
    comment: str
    created_at: datetime


class SickLeaveIn(BaseModel):
    date_from: date
    date_to: date
    comment: str = Field(default="", max_length=1000)


class SickLeaveOut(_Out):
    id: int
    user_id: int
    date_from: date
    date_to: date
    comment: str
    status: SickLeaveStatus
    created_at: datetime


class SickLeaveAdminOut(SickLeaveOut):
    employee_name: str = ""


class PayslipOut(_Out):
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
