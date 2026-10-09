"""Provider listing and detail endpoints.

Thin layer: routing + validation only. Data access goes through the
provider service (router -> provider service -> database -> MongoDB).
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.database import DatabaseUnavailableError
from app.schemas.provider import Provider, ProviderListResponse
from app.services import provider_service

router = APIRouter(tags=["Providers"])


@router.get(
    "/api/providers",
    response_model=ProviderListResponse,
    summary="Search demo healthcare providers",
    description=(
        "Search the clearly-labelled DEMO provider dataset stored in MongoDB. "
        "All filters are optional and combined with AND logic; text filters "
        "are case-insensitive. Healthcare navigation data only — this endpoint "
        "never diagnoses or recommends treatment. Returns HTTP 503 when the "
        "database is unreachable (no fabricated results)."
    ),
)
async def search_providers(
    specialization: str | None = Query(
        None, description="e.g. Dermatology (case-insensitive)", examples=["Dermatology"]
    ),
    city: str | None = Query(None, description="e.g. Bangalore", examples=["Bangalore"]),
    area: str | None = Query(None, description="Locality within the city", examples=["Indiranagar"]),
    maximum_budget: float | None = Query(
        None, gt=0, description="Maximum consultation fee in INR", examples=[700]
    ),
    minimum_rating: float | None = Query(
        None, ge=0, le=5, description="Minimum rating (0-5)", examples=[4.5]
    ),
    language: str | None = Query(None, description="Language spoken", examples=["Kannada"]),
    available_today: bool = Query(
        False, description="Only providers available on the current weekday"
    ),
) -> ProviderListResponse:
    """Return demo providers matching ALL supplied filters."""
    try:
        providers = await provider_service.search_providers(
            specialization=specialization,
            city=city,
            area=area,
            maximum_budget=maximum_budget,
            minimum_rating=minimum_rating,
            language=language,
            available_today=available_today,
        )
    except DatabaseUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return ProviderListResponse(count=len(providers), providers=providers)


@router.get(
    "/api/providers/{provider_id}",
    response_model=Provider,
    summary="Get a provider by id",
    description="Returns the complete demo provider record, or 404 if unknown.",
)
async def get_provider(provider_id: str) -> Provider:
    """Return one provider record by id."""
    try:
        provider = await provider_service.get_provider_by_id(provider_id)
    except DatabaseUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if provider is None:
        raise HTTPException(status_code=404, detail="Provider not found")
    return provider
