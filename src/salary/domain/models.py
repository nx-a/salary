"""Доменные сущности. Не зависят от фреймворков и инфраструктуры."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum

from salary.domain.errors import ValidationError


class Role(StrEnum):
    ADMIN = "admin"
    USER = "user"


class UserStatus(StrEnum):
    PENDING = "pending"
    ACTIVE = "active"
    REJECTED = "rejected"


class BonusKind(StrEnum):
    BONUS = "bonus"          # премия
    ALLOWANCE = "allowance"  # надбавка


class SickLeaveStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass
class User:
    login: str
    password_hash: str
    full_name: str
    role: Role = Role.USER
    status: UserStatus = UserStatus.PENDING
    base_salary: Decimal = Decimal("0.00")
    id: int | None = None
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def is_admin(self) -> bool:
        return self.role is Role.ADMIN

    @property
    def is_active(self) -> bool:
        return self.status is UserStatus.ACTIVE

    def verify(self) -> None:
        self.status = UserStatus.ACTIVE

    def reject(self) -> None:
        if self.is_admin:
            raise ValidationError("Нельзя отклонить администратора")
        self.status = UserStatus.REJECTED

    def set_base_salary(self, amount: Decimal) -> None:
        if amount < 0:
            raise ValidationError("Оклад не может быть отрицательным")
        self.base_salary = amount.quantize(Decimal("0.01"))


@dataclass
class Bonus:
    user_id: int
    amount: Decimal
    kind: BonusKind
    year: int
    month: int
    comment: str = ""
    id: int | None = None
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        if self.amount <= 0:
            raise ValidationError("Сумма премии/надбавки должна быть положительной")
        if not 1 <= self.month <= 12:
            raise ValidationError("Месяц должен быть от 1 до 12")
        self.amount = self.amount.quantize(Decimal("0.01"))


@dataclass
class SickLeave:
    user_id: int
    date_from: date
    date_to: date
    comment: str = ""
    status: SickLeaveStatus = SickLeaveStatus.PENDING
    id: int | None = None
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        if self.date_from > self.date_to:
            raise ValidationError("Дата начала больничного позже даты окончания")

    def overlaps(self, other: SickLeave) -> bool:
        return self.date_from <= other.date_to and other.date_from <= self.date_to

    @property
    def is_active(self) -> bool:
        """Учитывается ли больничный при проверке пересечений."""
        return self.status is not SickLeaveStatus.REJECTED

    def approve(self) -> None:
        self._ensure_pending()
        self.status = SickLeaveStatus.APPROVED

    def reject(self) -> None:
        self._ensure_pending()
        self.status = SickLeaveStatus.REJECTED

    def _ensure_pending(self) -> None:
        if self.status is not SickLeaveStatus.PENDING:
            raise ValidationError("Больничный уже рассмотрен")
