"""Configuration settings for CrewChief using Pydantic Settings."""

import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Application settings for CrewChief.

    Settings can be configured via:
    - Environment variables (prefixed with CREWCHIEF_)
    - .env file in the project root
    - Direct instantiation with kwargs
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="CREWCHIEF_",
        case_sensitive=False,
    )

    # Database settings
    db_path: str = "~/.crewchief/crewchief.db"

    # LLM settings
    llm_base_url: str = "http://localhost:1234/v1"
    llm_model: str = "phi-3.5-mini"
    llm_enabled: bool = True
    llm_timeout: int = 30

    def get_expanded_db_path(self) -> Path:
        """Get the database path with user home directory expanded."""
        return Path(os.path.expanduser(self.db_path))

    def ensure_config_dir(self) -> None:
        """Ensure the configuration directory exists."""
        db_path = self.get_expanded_db_path()
        db_path.parent.mkdir(parents=True, exist_ok=True)


# Global settings instance
_settings: AppSettings | None = None


def get_settings() -> AppSettings:
    """Get or create the global settings instance."""
    global _settings
    if _settings is None:
        _settings = AppSettings()
    return _settings


def reset_settings() -> None:
    """Reset the global settings instance (useful for testing)."""
    global _settings
    _settings = None
