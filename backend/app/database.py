"""MongoDB access layer (official PyMongo Async API).

Modes (``DATABASE_MODE``):
- ``mongodb`` (default): the application connects to MongoDB on startup and
  fails LOUDLY if it cannot — no silent fallback, no fake data.
- ``memory``: explicitly for unit tests only, so the test suite can run
  without a database (Stage 5 test strategy).

Connection lifecycle is managed by the FastAPI lifespan in ``main.py``
(connect on startup, close on shutdown). Credentials always come from
environment variables — never from committed code.
"""

from __future__ import annotations

import logging

from pymongo import AsyncMongoClient
from pymongo.errors import PyMongoError

from app.config import get_settings

logger = logging.getLogger("medaccess.database")


class DatabaseUnavailableError(RuntimeError):
    """Raised when MongoDB is required (mongodb mode) but unavailable.

    Carries a message that is safe to show via the API — no credentials,
    no connection strings.
    """


_client: AsyncMongoClient | None = None
_db = None


def database_mode() -> str:
    """Return the configured database mode ('mongodb' or 'memory')."""
    return get_settings().database_mode.strip().lower()


def is_memory_mode() -> bool:
    """True only when DATABASE_MODE=memory (unit tests)."""
    return database_mode() == "memory"


async def connect_database() -> None:
    """Create the MongoDB client and verify connectivity (startup hook).

    In mongodb mode a failed ping raises :class:`DatabaseUnavailableError`
    so the application clearly reports database failure instead of starting
    up against a database it cannot reach.
    """
    global _client, _db
    settings = get_settings()

    if is_memory_mode():
        logger.warning(
            "DATABASE_MODE=memory — serving the in-memory demo dataset. "
            "This mode is for unit tests only and stores nothing."
        )
        return

    if database_mode() != "mongodb":
        raise DatabaseUnavailableError(
            f"Unknown DATABASE_MODE '{settings.database_mode}'. Use 'mongodb' or 'memory'."
        )

    client = AsyncMongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=3000)
    try:
        await client.admin.command("ping")
    except PyMongoError as exc:
        logger.error("MongoDB startup ping failed: %s", exc)
        raise DatabaseUnavailableError(
            "MongoDB is unavailable. The application refuses to start in "
            "mongodb mode rather than pretend data exists. Start MongoDB with "
            "'docker compose up -d mongodb' and retry."
        ) from exc

    _client = client
    _db = client[settings.database_name]
    await _ensure_indexes()
    logger.info("Connected to MongoDB database '%s'.", settings.database_name)


async def disconnect_database() -> None:
    """Close the MongoDB client (shutdown hook)."""
    global _client, _db
    if _client is not None:
        await _client.close()  # AsyncMongoClient.close is a coroutine (pymongo >= 4.10)
        _client = None
        _db = None
        logger.info("MongoDB connection closed.")


async def ping_database() -> bool:
    """Ping MongoDB; True when reachable, False otherwise (never raises)."""
    if _client is None:
        return False
    try:
        await _client.admin.command("ping")
        return True
    except PyMongoError:
        return False


def get_database():
    """Return the database handle, or raise if not connected."""
    if _db is None:
        raise DatabaseUnavailableError(
            "Database is not connected (startup failed or DATABASE_MODE=memory)."
        )
    return _db


def get_providers_collection():
    """Return the ``providers`` collection (requires mongodb mode)."""
    return get_database()["providers"]


def get_users_collection():
    """Return the ``users`` collection (empty placeholder in Stage 5)."""
    return get_database()["users"]


async def _ensure_indexes() -> None:
    """Create collections and query-supporting indexes (idempotent).

    Indexes cover the fields actually filtered on: city, specialization,
    consultation_fee and rating, plus a unique index on the stable id.
    """
    providers = get_database()["providers"]
    await providers.create_index("id", unique=True)
    await providers.create_index("city")
    await providers.create_index("specialization")
    await providers.create_index("consultation_fee")
    await providers.create_index("rating")
    users = get_database()["users"]
    await users.create_index("email", unique=True)
