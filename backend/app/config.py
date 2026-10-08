"""Application configuration loaded from environment variables.

Values come from process environment and, optionally, a local ``.env`` file
(see ``.env.example`` at the repository root). Secrets are never hardcoded.
"""

from functools import lru_cache

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

    # --- MongoDB (wired up in Stage 5) ---
    mongodb_uri: str = "mongodb://localhost:27017"
    database_name: str = "medaccess"

    # --- Authentication / JWT (wired up in Stage 5) ---
    # Placeholder only; replace via environment variable in real deployments.
    secret_key: str = "insecure-dev-only-change-me-via-env"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # --- AI / LLM provider (wired up in Stage 7) ---
    # Empty key => the deterministic fallback parser is used locally.
    llm_api_key: str = ""
    llm_model: str = ""
    llm_base_url: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        """CORS origins as a list, parsed from the comma-separated env value."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (env is read once per process)."""
    return Settings()
