from functools import lru_cache
from pathlib import Path
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    app_name: str = "库存管理系统 API"
    app_version: str = "1.0.0"
    api_v1_prefix: str = "/api/v1"
    debug: bool = False

    pg_username: str = "postgres"
    pg_password: str = "postgres"
    pg_host: str = "localhost"
    pg_port: int = 5432
    pg_database: str = "stockpilot_db"

    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @property
    def database_url(self) -> str:
        user = quote_plus(self.pg_username)
        password = quote_plus(self.pg_password)
        return (
            f"postgresql+psycopg://{user}:{password}@"
            f"{self.pg_host}:{self.pg_port}/{self.pg_database}"
        )

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
