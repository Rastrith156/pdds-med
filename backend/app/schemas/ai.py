"""Schemas for the natural-language AI search endpoint (Stage 7).

The response echoes the validated structured request plus ranked results.
The AI layer only parses — ranking always comes from the deterministic
recommendation engine, and provider data always comes from the database.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from ai.base import ParsedHealthcareQuery

from app.schemas.recommendation import RecommendationItem


class AISearchRequest(BaseModel):
    """A free-text healthcare-navigation request."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"query": "I need a dermatologist near Bangalore under ₹700 today"}
        }
    )

    query: str = Field(
        ...,
        max_length=1000,
        description="Natural-language navigation request (never medical advice).",
    )


class AISearchResponse(BaseModel):
    """Structured parse + ranked recommendations, or a safety/guidance message."""

    query: str = Field(..., description="Echo of the original user query")
    parser: str = Field(
        ..., description="Parser that produced the result: 'llm' or 'fallback'"
    )
    parsed_request: ParsedHealthcareQuery | None = Field(
        None,
        description="Validated search parameters; null when refused or guided",
    )
    message: str | None = Field(
        None,
        description="Safety refusal or guidance message when no search was run",
    )
    count: int = Field(..., description="Number of recommendations returned")
    recommendations: list[RecommendationItem] = Field(
        default_factory=list,
        description="Ranked providers produced by the deterministic engine",
    )
