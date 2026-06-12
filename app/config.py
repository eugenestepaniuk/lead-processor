"""Application configuration — single source of truth for all settings.

All configuration is read from environment variables (or an .env file).
No other module should read os.environ directly; use get_settings() instead.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Project-wide settings loaded from environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Server ---
    port: int = 8000
    log_level: str = "info"
    app_env: str = "development"
    # Comma-separated list of allowed CORS origins (e.g. https://your-landing.example.com).
    # Empty by default — no cross-origin access permitted.
    cors_origins: str = ""

    # --- AI (Gemini) ---
    ai_enabled: bool = True
    gemini_api_key: str | None = None
    ai_model: str = "gemini-2.5-flash"

    # --- Storage ---
    sqlite_path: str = "./data/leads.db"

    # --- Telegram ---
    telegram_enabled: bool = True
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None

    @model_validator(mode="after")
    def _check_required_secrets(self) -> Settings:
        """Fail fast when a feature toggle is on but its secret is missing."""

        def _is_empty(value: str | None) -> bool:
            return value is None or not value.strip()

        if self.ai_enabled and _is_empty(self.gemini_api_key):
            raise ValueError(
                "AI is enabled (AI_ENABLED=true) but GEMINI_API_KEY is not set. "
                "Provide a non-empty GEMINI_API_KEY or set AI_ENABLED=false."
            )

        if self.telegram_enabled:
            missing: list[str] = []
            if _is_empty(self.telegram_bot_token):
                missing.append("TELEGRAM_BOT_TOKEN")
            if _is_empty(self.telegram_chat_id):
                missing.append("TELEGRAM_CHAT_ID")
            if missing:
                raise ValueError(
                    f"Telegram is enabled (TELEGRAM_ENABLED=true) but the following "
                    f"variable(s) are not set: {', '.join(missing)}. "
                    f"Provide non-empty values or set TELEGRAM_ENABLED=false."
                )

        return self


@lru_cache
def get_settings() -> Settings:
    """Return the cached Settings instance (created once per process)."""
    return Settings()
