from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=PROJECT_ROOT / ".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/salary"
    jwt_secret: str = "change-me"
    jwt_ttl_minutes: int = 60
    admin_login: str = "admin"
    admin_password: str = "admin123"
    static_dir: Path = PROJECT_ROOT / "static"


@lru_cache
def get_settings() -> Settings:
    return Settings()
