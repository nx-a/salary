"""Доменные исключения."""


class DomainError(Exception):
    """Базовое исключение предметной области."""


class ValidationError(DomainError):
    """Нарушено бизнес-правило."""


class NotFoundError(DomainError):
    """Объект не найден."""


class AlreadyExistsError(DomainError):
    """Объект уже существует."""


class AuthenticationError(DomainError):
    """Неверные учётные данные или токен."""


class AccessDeniedError(DomainError):
    """Недостаточно прав или учётная запись не подтверждена."""
