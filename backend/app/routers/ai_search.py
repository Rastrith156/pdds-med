"""Natural-language AI search endpoint (Stage 7).

Flow:
    POST /api/ai/search
        -> ai.parse_query   (safety guardrail -> LLM if configured -> fallback)
        -> provider_service (hard filters, MongoDB)
        -> recommendation_service (deterministic weighted ranking)
        -> AISearchResponse

The AI layer ONLY extracts search parameters. It never ranks providers,
never diagnoses, never prescribes, and never sees provider records, the
database, or API keys (the backend calls the LLM — never the browser).
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from ai import parse_query

from app.database import DatabaseUnavailableError
from app.schemas.ai import AISearchRequest, AISearchResponse
from app.services import provider_service, recommendation_service

logger = logging.getLogger("medaccess.ai.api")

router = APIRouter(tags=["AI Search"])

#: How many ranked results a natural-language search returns.
AI_RESULT_LIMIT = 5


@router.post(
    "/api/ai/search",
    response_model=AISearchResponse,
    summary="Search providers from a natural-language request",
    description=(
        "Parses a free-text healthcare-navigation request into structured "
        "search parameters (LLM when configured, deterministic fallback "
        "otherwise), applies them as hard filters, and ranks the matches "
        "with the deterministic recommendation engine. "
        "Diagnosis/medication/treatment requests are refused with a safe "
        "navigation message before any parsing happens. The AI never "
        "calculates match scores and never provides medical advice."
    ),
)
async def ai_search(request: AISearchRequest) -> AISearchResponse:
    """Parse one query safely, then filter + rank providers deterministically."""
    # Log metadata only — never the raw query (it may contain health info).
    logger.info("ai search received (query_len=%d)", len(request.query))

    outcome = await parse_query(request.query)

    if outcome.refusal is not None:
        logger.info("ai search refused by safety guardrail (parser=%s)", outcome.parser)
        return AISearchResponse(
            query=request.query,
            parser=outcome.parser,
            parsed_request=None,
            message=outcome.refusal,
            count=0,
            recommendations=[],
        )

    if outcome.parsed is None:
        # No usable criteria extracted — ask the user for the basics.
        logger.info("ai search returned guidance (parser=%s)", outcome.parser)
        return AISearchResponse(
            query=request.query,
            parser=outcome.parser,
            parsed_request=None,
            message=outcome.guidance,
            count=0,
            recommendations=[],
        )

    parsed = outcome.parsed
    try:
        matching = await provider_service.search_providers(
            specialization=parsed.specialization,
            city=parsed.city,
            area=parsed.area,
            maximum_budget=parsed.maximum_budget,
            minimum_rating=parsed.minimum_rating,
            language=parsed.language,
            available_today=parsed.available_today,
        )
    except DatabaseUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    # Ranking stays with the deterministic engine — the AI never scores.
    recommendations = recommendation_service.recommend_providers(
        matching,
        budget=parsed.maximum_budget,
        latitude=parsed.latitude,
        longitude=parsed.longitude,
        available_today=parsed.available_today,
        language=parsed.language,
        limit=AI_RESULT_LIMIT,
    )

    logger.info(
        "ai search complete (parser=%s, matches=%d, recommendations=%d)",
        outcome.parser,
        len(matching),
        len(recommendations),
    )
    return AISearchResponse(
        query=request.query,
        parser=outcome.parser,
        parsed_request=parsed,
        message=None,
        count=len(recommendations),
        recommendations=recommendations,
    )
