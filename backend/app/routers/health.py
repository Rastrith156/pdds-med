"""Health check router."""

from fastapi import APIRouter

from app import database
from app.schemas.health import DatabaseHealthResponse, HealthResponse

router = APIRouter(tags=["Health"])


@router.get(
    "/api/health",
    response_model=HealthResponse,
    summary="Service health check",
    description=(
        "Liveness status of the MediAccess AI backend. Reports 'degraded' "
        "when MongoDB is required but unreachable — it never claims health "
        "it does not have."
    ),
)
async def get_health() -> HealthResponse:
    """Report service liveness, honestly reflecting database reachability."""
    if database.is_memory_mode():
        return HealthResponse(status="healthy", service="MediAccess AI")
    if await database.ping_database():
        return HealthResponse(status="healthy", service="MediAccess AI")
    return HealthResponse(status="degraded", service="MediAccess AI")


@router.get(
    "/api/health/database",
    response_model=DatabaseHealthResponse,
    summary="Database health check",
    description=(
        "Reports whether MongoDB is reachable. Exposes no credentials or "
        "connection strings."
    ),
)
async def get_database_health() -> DatabaseHealthResponse:
    """Ping MongoDB and report the result without leaking configuration."""
    if database.is_memory_mode():
        return DatabaseHealthResponse(status="healthy", database="memory")
    if await database.ping_database():
        return DatabaseHealthResponse(status="healthy", database="mongodb")
    return DatabaseHealthResponse(status="unhealthy", database="unavailable")
