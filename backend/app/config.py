from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration, read from environment variables (or a .env file)."""

    model_config = SettingsConfigDict(env_file=Path(__file__).resolve().parent.parent / ".env", env_prefix="CLEARWAVE_")

    database_url: str = "postgresql+asyncpg://clearwave:clearwave@localhost:5433/clearwave"
    # Where the front end is served from, so the browser may call the API with the session cookie.
    frontend_origin: str = "http://localhost:5173"
    cookie_secure: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()


