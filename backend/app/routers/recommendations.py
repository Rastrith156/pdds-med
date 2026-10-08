"""Recommendation endpoint — deterministic ranking, no LLM.

Flow: router -> provider_service (hard filters) -> recommendation_service
      (weighted scoring) -> response schemas.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas.recommendation import RecommendationRequest, RecommendationResponse
from app.services import provider_service, recommendation_service

router = APIRouter(tags=["Recommendations"])


@router.post(
    "/api/recommendations",
    response_model=RecommendationResponse,
    summary="Get ranked provider recommendations",
    description=(
        "Ranks demo healthcare providers with a deterministic weighted formula "
        "(budget 30%, distance 25%, availability 20%, rating 15%, language "
        "10%). Constraints in the request are applied as hard filters first. "
        "Healthcare navigation only — this endpoint never diagnoses conditions "
        "or gives treatment advice, and uses no LLM."
    ),
)
def create_recommendations(request: RecommendationRequest) -> RecommendationResponse:
    """Filter providers, score them, sort by score, and return the top N."""
    matching = provider_service.search_providers(
        specialization=request.specialization,
        city=request.city,
        area=request.area,
        maximum_budget=request.maximum_budget,
        minimum_rating=request.minimum_rating,
        language=request.language,
        available_today=request.available_today,
    )
    recommendations = recommendation_service.recommend_providers(
        matching,
        budget=request.maximum_budget,
        latitude=request.latitude,
        longitude=request.longitude,
        available_today=request.available_today,
        language=request.language,
        limit=request.limit,
    )
    return RecommendationResponse(count=len(recommendations), recommendations=recommendations)
