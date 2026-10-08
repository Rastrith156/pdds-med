"""Schemas for the health endpoint."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Response body of ``GET /api/health``."""

    status: str
    service: str
