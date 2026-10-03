"""Реализация портов хранения на PostgreSQL через SQLAlchemy."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from salary.adapters.outbound.persistence.orm import BonusRow, SickLeaveRow, UserRow
from salary.application.ports.repositories import (
    BonusRepository,
    SickLeaveRepository,
    UnitOfWork,
    UserRepository,
)
from salary.domain.models import (
    Bonus,
    BonusKind,
    Role,
    SickLeave,
    SickLeaveStatus,
    User,
    UserStatus,
)


def _user_to_domain(row: UserRow) -> User:
    return User(
        id=row.id,
        login=row.login,
        password_hash=row.password_hash,
        full_name=row.full_name,
        role=Role(row.role),
        status=UserStatus(row.status),
        base_salary=row.base_salary,
        created_at=row.created_at,
    )


def _bonus_to_domain(row: BonusRow) -> Bonus:
    return Bonus(
        id=row.id,
        user_id=row.user_id,
        amount=row.amount,
        kind=BonusKind(row.kind),
        year=row.year,
        month=row.month,
        comment=row.comment,
        created_at=row.created_at,
    )


def _leave_to_domain(row: SickLeaveRow) -> SickLeave:
    return SickLeave(
        id=row.id,
        user_id=row.user_id,
        date_from=row.date_from,
        date_to=row.date_to,
        comment=row.comment,
        status=SickLeaveStatus(row.status),
        created_at=row.created_at,
    )


class SqlUserRepository(UserRepository):
    def __init__(self, session: Session) -> None:
        self._s = session

    def add(self, user: User) -> User:
        row = UserRow(
            login=user.login,
            password_hash=user.password_hash,
            full_name=user.full_name,
            role=user.role.value,
            status=user.status.value,
            base_salary=user.base_salary,
            created_at=user.created_at,
        )
        self._s.add(row)
        self._s.flush()
        return _user_to_domain(row)

    def update(self, user: User) -> User:
        row = self._s.get_one(UserRow, user.id)
        row.full_name = user.full_name
        row.password_hash = user.password_hash
        row.role = user.role.value
        row.status = user.status.value
        row.base_salary = user.base_salary
        self._s.flush()
        return _user_to_domain(row)

    def get(self, user_id: int) -> User | None:
        row = self._s.get(UserRow, user_id)
        return _user_to_domain(row) if row else None

    def get_by_login(self, login: str) -> User | None:
        row = self._s.scalar(select(UserRow).where(UserRow.login == login))
        return _user_to_domain(row) if row else None

    def list(self, status: UserStatus | None = None) -> list[User]:
        query = select(UserRow).order_by(UserRow.full_name)
        if status:
            query = query.where(UserRow.status == status.value)
        return [_user_to_domain(r) for r in self._s.scalars(query)]


class SqlBonusRepository(BonusRepository):
    def __init__(self, session: Session) -> None:
        self._s = session

    def add(self, bonus: Bonus) -> Bonus:
        row = BonusRow(
            user_id=bonus.user_id,
            amount=bonus.amount,
            kind=bonus.kind.value,
            year=bonus.year,
            month=bonus.month,
            comment=bonus.comment,
            created_at=bonus.created_at,
        )
        self._s.add(row)
        self._s.flush()
        return _bonus_to_domain(row)

    def get(self, bonus_id: int) -> Bonus | None:
        row = self._s.get(BonusRow, bonus_id)
        return _bonus_to_domain(row) if row else None

    def delete(self, bonus_id: int) -> None:
        row = self._s.get(BonusRow, bonus_id)
        if row:
            self._s.delete(row)
            self._s.flush()

    def list_for_user(self, user_id: int, year: int | None = None, month: int | None = None) -> list[Bonus]:
        query = select(BonusRow).where(BonusRow.user_id == user_id)
        if year is not None:
            query = query.where(BonusRow.year == year)
        if month is not None:
            query = query.where(BonusRow.month == month)
        query = query.order_by(BonusRow.year.desc(), BonusRow.month.desc(), BonusRow.id.desc())
        return [_bonus_to_domain(r) for r in self._s.scalars(query)]


class SqlSickLeaveRepository(SickLeaveRepository):
    def __init__(self, session: Session) -> None:
        self._s = session

    def add(self, leave: SickLeave) -> SickLeave:
        row = SickLeaveRow(
            user_id=leave.user_id,
            date_from=leave.date_from,
            date_to=leave.date_to,
            comment=leave.comment,
            status=leave.status.value,
            created_at=leave.created_at,
        )
        self._s.add(row)
        self._s.flush()
        return _leave_to_domain(row)

    def update(self, leave: SickLeave) -> SickLeave:
        row = self._s.get_one(SickLeaveRow, leave.id)
        row.date_from = leave.date_from
        row.date_to = leave.date_to
        row.comment = leave.comment
        row.status = leave.status.value
        self._s.flush()
        return _leave_to_domain(row)

    def get(self, leave_id: int) -> SickLeave | None:
        row = self._s.get(SickLeaveRow, leave_id)
        return _leave_to_domain(row) if row else None

    def list_for_user(self, user_id: int) -> list[SickLeave]:
        query = select(SickLeaveRow).where(SickLeaveRow.user_id == user_id).order_by(SickLeaveRow.date_from.desc())
        return [_leave_to_domain(r) for r in self._s.scalars(query)]

    def list(self, status: SickLeaveStatus | None = None) -> list[SickLeave]:
        query = select(SickLeaveRow).order_by(SickLeaveRow.date_from.desc())
        if status:
            query = query.where(SickLeaveRow.status == status.value)
        return [_leave_to_domain(r) for r in self._s.scalars(query)]


class SqlUnitOfWork(UnitOfWork):
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session = session_factory()
        self.users = SqlUserRepository(self._session)
        self.bonuses = SqlBonusRepository(self._session)
        self.sick_leaves = SqlSickLeaveRepository(self._session)

    def __exit__(self, exc_type, exc, tb) -> None:
        try:
            super().__exit__(exc_type, exc, tb)
        finally:
            self._session.close()

    def commit(self) -> None:
        self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()
