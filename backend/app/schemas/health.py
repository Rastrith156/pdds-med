"""Schemas for the health endpoints."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Response body of ``GET /api/health``.

    ``status`` is ``healthy`` during normal operation and ``degraded`` when
    MongoDB is required but unreachable — the service never pretends the
    database is fine.
    """

    status: str
    service: str


class DatabaseHealthResponse(BaseModel):
    """Response body of ``GET /api/health/database``.

    Never exposes credentials or connection strings.
    """

    status: str
    database: str
