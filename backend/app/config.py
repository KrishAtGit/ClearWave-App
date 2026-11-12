from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal
from pydantic import SecretStr

class Settings(BaseSettings):
    """Configuration, read from environment variables (or a .env file)."""

    model_config = SettingsConfigDict(env_file=Path(__file__).resolve().parent.parent / ".env", env_prefix="CLEARWAVE_")

    database_url: str = "postgresql+asyncpg://clearwave:clearwave@localhost:5433/clearwave"
    # Where the front end is served from, so the browser may call the API with the session cookie.
    frontend_origin: str = "http://localhost:5173"
    cookie_secure: bool = False

    # azurtite published deployment key
    storage_connection_string: str = (
        "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;"
        "AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;"
        "BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;"
    )
    storage_container: str = "samples"
    max_upload_mb: int = 20

    matcher: Literal["fake", "acrcloud"] = "fake"
    acr_host: str = ""
    acr_access_key: str = ""
    acr_access_secret: SecretStr = SecretStr("")

    # average pay out per stream in us bucks
    payout_per_stream: float = 0.004


@lru_cache
def get_settings() -> Settings:
    return Settings()


