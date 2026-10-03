"""Служебные команды: `python -m salary.cli <команда>`."""
from __future__ import annotations

import argparse
import sys

from salary.adapters.outbound.persistence.database import create_database, create_schema, drop_schema
from salary.config import get_settings
from salary.container import Container


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="salary")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("db-create", help="создать базу данных")
    sub.add_parser("migrate", help="создать таблицы")
    sub.add_parser("db-drop-schema", help="удалить все таблицы сервиса")
    admin = sub.add_parser("create-admin", help="создать администратора")
    admin.add_argument("--login")
    admin.add_argument("--password")
    args = parser.parse_args(argv)

    settings = get_settings()
    match args.command:
        case "db-create":
            created = create_database(settings.database_url)
            print("База данных создана" if created else "База данных уже существует")
        case "migrate":
            container = Container.build(settings)
            create_schema(container.engine)
            print("Схема создана")
        case "db-drop-schema":
            drop_schema(Container.build(settings).engine)
            print("Схема удалена")
        case "create-admin":
            container = Container.build(settings)
            user = container.auth.ensure_admin(
                args.login or settings.admin_login, args.password or settings.admin_password
            )
            print(f"Администратор: {user.login} (id={user.id})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
