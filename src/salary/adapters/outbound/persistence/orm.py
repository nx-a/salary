"""ORM-модели SQLAlchemy (деталь инфраструктуры, в домен не протекают)."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class UserRow(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    login: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(128))
    full_name: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(16))
    status: Mapped[str] = mapped_column(String(16), index=True)
    base_salary: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    created_at: Mapped[datetime] = mapped_column(DateTime)


class BonusRow(Base):
    __tablename__ = "bonuses"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_bonus_amount_positive"),
        CheckConstraint("month BETWEEN 1 AND 12", name="ck_bonus_month"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    kind: Mapped[str] = mapped_column(String(16))
    year: Mapped[int] = mapped_column(Integer)
    month: Mapped[int] = mapped_column(Integer)
    comment: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime)


class SickLeaveRow(Base):
    __tablename__ = "sick_leaves"
    __table_args__ = (CheckConstraint("date_from <= date_to", name="ck_sick_leave_dates"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    date_from: Mapped[date] = mapped_column(Date)
    date_to: Mapped[date] = mapped_column(Date)
    comment: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(16), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime)
