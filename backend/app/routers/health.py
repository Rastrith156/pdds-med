"""Health check router."""

from fastapi import APIRouter

from app.schemas.health import HealthResponse

router = APIRouter(tags=["Health"])


@router.get(
    "/api/health",
    response_model=HealthResponse,
    summary="Service health check",
    description="Returns the liveness status of the MediAccess AI backend.",
)
def get_health() -> HealthResponse:
    """Report that the service is running."""
    return HealthResponse(status="healthy", service="MediAccess AI")
