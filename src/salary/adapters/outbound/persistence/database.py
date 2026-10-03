"""Подключение к PostgreSQL, создание БД и схемы."""
from __future__ import annotations

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from salary.adapters.outbound.persistence.orm import Base


def make_engine(url: str) -> Engine:
    return create_engine(url, pool_pre_ping=True)


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(engine, expire_on_commit=False)


def create_database(url: str) -> bool:
    """Создаёт базу данных из URL, если её нет. Возвращает True, если создана."""
    target = make_url(url)
    admin_engine = create_engine(target.set(database="postgres"), isolation_level="AUTOCOMMIT")
    try:
        with admin_engine.connect() as conn:
            exists = conn.scalar(text("SELECT 1 FROM pg_database WHERE datname = :n"), {"n": target.database})
            if exists:
                return False
            conn.execute(text(f'CREATE DATABASE "{target.database}"'))
            return True
    finally:
        admin_engine.dispose()


def create_schema(engine: Engine) -> None:
    Base.metadata.create_all(engine)


def drop_schema(engine: Engine) -> None:
    Base.metadata.drop_all(engine)
