"""Schemas for the recommendation API (Stage 4)."""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from app.schemas.provider import Provider


class RecommendationRequest(BaseModel):
    """Structured healthcare-navigation request for POST /api/recommendations.

    All fields are optional. Constraints supplied here are applied as hard
    filters; the engine then ranks the matching providers. This schema accepts
    navigation preferences only — never symptoms or clinical information.
    """

    specialization: str | None = Field(None, examples=["Dermatology"], description="Provider specialization filter")
    city: str | None = Field(None, examples=["Bangalore"], description="City filter")
    area: str | None = Field(None, examples=["Indiranagar"], description="Locality filter")
    maximum_budget: float | None = Field(None, gt=0, examples=[700], description="Maximum consultation fee in INR")
    minimum_rating: float | None = Field(None, ge=0, le=5, examples=[4.0], description="Minimum rating (0-5)")
    language: str | None = Field(None, examples=["Kannada"], description="Preferred language spoken by the provider")
    available_today: bool = Field(False, description="Only providers available on the current weekday")
    latitude: float | None = Field(None, ge=-90, le=90, description="User latitude for distance scoring")
    longitude: float | None = Field(None, ge=-180, le=180, description="User longitude for distance scoring")
    limit: int = Field(10, ge=1, le=20, description="Maximum number of recommendations (1-20)")

    @model_validator(mode="after")
    def _require_paired_coordinates(self) -> RecommendationRequest:
        """Location must be supplied as both latitude AND longitude, or neither."""
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("Both latitude and longitude must be supplied together.")
        return self


class ScoreBreakdown(BaseModel):
    """Normalized component scores (each 0-100) behind the final match score."""

    budget: int = Field(..., ge=0, le=100)
    distance: int = Field(..., ge=0, le=100)
    availability: int = Field(..., ge=0, le=100)
    rating: int = Field(..., ge=0, le=100)
    language: int = Field(..., ge=0, le=100)


class RecommendationItem(BaseModel):
    """One ranked provider with its score, breakdown and generated reasons."""

    provider: Provider
    match_score: int = Field(..., ge=0, le=100, description="Weighted total score, 0-100")
    distance_km: float | None = Field(
        None, description="Haversine distance in km; null when no coordinates were supplied"
    )
    score_breakdown: ScoreBreakdown
    reasons: list[str] = Field(..., description="Human-readable reasons generated from the scoring data")


class RecommendationResponse(BaseModel):
    """Response envelope for POST /api/recommendations."""

    count: int = Field(..., description="Number of recommendations returned")
    recommendations: list[RecommendationItem]


__all__ = [
    "RecommendationRequest",
    "ScoreBreakdown",
    "RecommendationItem",
    "RecommendationResponse",
]
