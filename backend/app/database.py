"""MongoDB access layer.

Stage 5 connects MongoDB (running via Docker) here. Until that stage is
implemented, any database access fails loudly with a clear message instead of
silently pretending the database works.
"""

from app.config import get_settings


class DatabaseNotConfiguredError(RuntimeError):
    """Raised when database access is attempted before Stage 5 is implemented."""


def get_database():
    """Return the database handle. NOT YET IMPLEMENTED (Stage 5).

    Raises:
        DatabaseNotConfiguredError: always, until MongoDB wiring lands in Stage 5.
    """
    settings = get_settings()
    raise DatabaseNotConfiguredError(
        "MongoDB integration is not implemented yet (Stage 5). "
        f"Configured URI: '{settings.mongodb_uri}', "
        f"database: '{settings.database_name}'. "
        "Start MongoDB with 'docker compose up -d' once Stage 5 lands."
    )
