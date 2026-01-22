"""Configuration settings using Pydantic."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    telegram_bot_token: str
    iron_api_key: str
    database_url: str = "sqlite+aiosqlite:///./select.db"
    iron_api_base_url: str = "https://api.sandbox.iron.xyz/api"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()
