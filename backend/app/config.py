from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, overridable via environment variables or backend/.env.

    Postgres is the intended database for persistent data. The default is a local
    SQLite file so development works with zero infrastructure; point DATABASE_URL
    at Postgres (see docker-compose.yml) when available.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "sqlite:///./data/headsup.db"
    cors_origins: str = "http://localhost:5173"
    materials_dir: str = "./data/materials"
    max_material_bytes: int = 20 * 1024 * 1024

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
