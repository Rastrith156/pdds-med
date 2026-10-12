"""Application configuration loaded from environment variables.

Values come from process environment and, optionally, a local ``.env`` file
(see ``.env.example`` at the repository root). Secrets are never hardcoded.
"""

from functools import lru_cache
from urllib.parse import urlparse

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central settings for the MediAccess AI backend."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Application ---
    app_env: str = "development"
    backend_host: str = "127.0.0.1"
    backend_port: int = 8000
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # --- MongoDB (Stage 5) ---
    # "mongodb" (default) = real MongoDB via Docker; "memory" = in-memory
    # demo dataset, ONLY for keeping unit tests independent of the database.
    database_mode: str = "mongodb"
    mongodb_uri: str = "mongodb://localhost:27017"
    database_name: str = "medaccess"

    # --- Authentication / JWT (reserved for a later stage) ---
    # Environment placeholders only — no auth is implemented yet. Replace the
    # secret via environment variable in real deployments; never commit secrets.
    secret_key: str = "insecure-dev-only-change-me-via-env"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # --- AI / LLM provider (wired up in Stage 7) ---
    # Empty key => the deterministic fallback parser is used locally.
    llm_api_key: str = ""
    llm_model: str = ""
    llm_base_url: str = ""

    # --- OpenProject (optional external integration) ---
    openproject_url: str = ""
    openproject_api_key: SecretStr = SecretStr("")
    openproject_project_id: str = ""

    @property
    def openproject_configured(self) -> bool:
        """Whether a safe OpenProject URL, API key, and numeric project id exist."""
        try:
            parsed = urlparse(self.openproject_url.strip())
            parsed.port
        except ValueError:
            return False
        return bool(
            parsed.scheme in {"http", "https"}
            and parsed.hostname
            and not parsed.username
            and not parsed.password
            and not parsed.query
            and not parsed.fragment
            and self.openproject_api_key.get_secret_value().strip()
            and self.openproject_project_id.strip().isdigit()
        )

    @property
    def cors_origin_list(self) -> list[str]:
        """CORS origins as a list, parsed from the comma-separated env value."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (env is read once per process)."""
    return Settings()
