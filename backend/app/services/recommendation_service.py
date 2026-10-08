"""Deterministic recommendation engine (Stage 4).

Scores providers on a 0-100 scale using a fixed, transparent weighted formula.
NO LLM is involved — identical inputs always produce identical output.

Scoring model
-------------
    match_score = budget      * 0.30   # fee vs the user's maximum budget
                + distance     * 0.25   # Haversine distance to user coordinates
                + availability * 0.20   # available today (when requested)
                + rating       * 0.15   # provider rating (0-5 -> 0-100)
                + language     * 0.10   # preferred language supported

Each component is normalized to 0-100. When a preference is NOT supplied the
component returns NEUTRAL_SCORE (50), so unconstrained dimensions neither
reward nor penalize providers. The final score is rounded to an integer.

Component formulas
------------------
budget:       fee <= budget           -> 100 (full score, incl. exact match)
              fee  > budget           -> 100 * budget / fee
                                          (proportional decay: fee = 2x budget
                                           -> 50, fee = 10x budget -> 10)
              budget not supplied     -> 50 (neutral)
distance:     <= 2 km                 -> 100
              >  2 km                 -> 100 * 0.5 ** ((km - 2) / 8)
                                          (8 km half-life beyond the first 2 km)
              no coordinates          -> 50 (neutral; distance_km stays null —
                                          a distance is never invented)
availability: requested + available    -> 100
              requested + unavailable  -> 0
              not requested           -> 50 (neutral)
rating:       rating / 5 * 100         (5.0 -> 100, 4.5 -> 90, 3.5 -> 70)
language:     requested + supported    -> 100 (case-insensitive)
              requested + unsupported  -> 0
              not requested           -> 50 (neutral)

This module is deliberately independent from FastAPI so the algorithm can be
unit-tested without starting a server.
"""

from __future__ import annotations

import math
from datetime import datetime

from app.schemas.provider import Provider
from app.schemas.recommendation import RecommendationItem, ScoreBreakdown

NEUTRAL_SCORE = 50.0
WEIGHTS: dict[str, float] = {
    "budget": 0.30,
    "distance": 0.25,
    "availability": 0.20,
    "rating": 0.15,
    "language": 0.10,
}
_EARTH_RADIUS_KM = 6371.0
_NEARBY_KM = 5.0
_REASONABLE_KM = 15.0


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance between two WGS-84 points, in kilometres."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lng2 - lng1)
    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    return 2 * _EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def budget_score(consultation_fee: float, maximum_budget: float | None) -> float:
    """See module docstring: 100 within budget, 100*budget/fee above, else 50."""
    if maximum_budget is None:
        return NEUTRAL_SCORE
    if consultation_fee <= maximum_budget:
        return 100.0
    return 100.0 * maximum_budget / consultation_fee


def distance_score(distance_km: float | None) -> float:
    """See module docstring: 100 within 2 km, then 8 km-half-life decay."""
    if distance_km is None:
        return NEUTRAL_SCORE
    if distance_km <= 2.0:
        return 100.0
    return 100.0 * (0.5 ** ((distance_km - 2.0) / 8.0))


def availability_score(is_available_today: bool, requested: bool) -> float:
    """100/0 only when availability was requested; neutral otherwise."""
    if not requested:
        return NEUTRAL_SCORE
    return 100.0 if is_available_today else 0.0


def rating_score(rating: float) -> float:
    """Convert a 0-5 rating to 0-100 (rating / 5 * 100)."""
    return rating / 5.0 * 100.0


def language_score(provider_languages: list[str], preferred_language: str | None) -> float:
    """100 when the preferred language matches (case-insensitive), else 0/neutral."""
    if preferred_language is None or not preferred_language.strip():
        return NEUTRAL_SCORE
    wanted = preferred_language.strip().casefold()
    return 100.0 if any(wanted == lang.strip().casefold() for lang in provider_languages) else 0.0


def _is_available_today(provider: Provider, day_name: str) -> bool:
    wanted = day_name.strip().casefold()
    return any(day.strip().casefold() == wanted for day in provider.available_days)


def _build_reasons(
    provider: Provider,
    *,
    budget: float | None,
    distance_km: float | None,
    requested_today: bool,
    is_available: bool,
    language: str | None,
    rating_s: float,
) -> list[str]:
    """Generate human-readable reasons directly from the scoring inputs."""
    reasons: list[str] = []
    if budget is not None and provider.consultation_fee <= budget:
        reasons.append("Within your requested budget")
    if requested_today and is_available:
        reasons.append("Available today")
    if rating_s >= 90:
        reasons.append("High provider rating")
    elif rating_s >= 80:
        reasons.append("Good provider rating")
    if language is not None and language.strip():
        if language_score(provider.languages, language) == 100.0:
            reasons.append("Matches your preferred language")
    if distance_km is None:
        reasons.append("Distance not calculated (no location provided)")
    elif distance_km <= _NEARBY_KM:
        reasons.append("Located nearby")
    elif distance_km <= _REASONABLE_KM:
        reasons.append("Within reasonable travel distance")
    return reasons


def recommend_providers(
    providers: list[Provider],
    *,
    budget: float | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    available_today: bool = False,
    language: str | None = None,
    limit: int = 10,
    today: str | None = None,
) -> list[RecommendationItem]:
    """Score, rank and return the top ``limit`` providers (deterministic).

    Args:
        providers: Candidate providers (filtering is the caller's job).
        budget: User's maximum consultation fee, if any.
        latitude/longitude: User coordinates; both or neither.
        available_today: Whether same-day availability is required.
        language: Preferred language, if any.
        limit: Maximum items to return.
        today: Weekday override for tests; defaults to the current weekday.

    Returns:
        Ranked items sorted by match_score desc, then rating desc,
        then consultation_fee asc, then provider id asc (stable ties).
    """
    day_name = (today or datetime.now().strftime("%A")).strip()

    results: list[RecommendationItem] = []
    for provider in providers:
        distance_km: float | None = None
        if latitude is not None and longitude is not None:
            distance_km = haversine_km(latitude, longitude, provider.latitude, provider.longitude)

        available = _is_available_today(provider, day_name)
        components = {
            "budget": budget_score(provider.consultation_fee, budget),
            "distance": distance_score(distance_km),
            "availability": availability_score(available, available_today),
            "rating": rating_score(provider.rating),
            "language": language_score(provider.languages, language),
        }
        total = sum(components[name] * WEIGHTS[name] for name in WEIGHTS)

        results.append(
            RecommendationItem(
                provider=provider,
                match_score=int(round(total)),
                distance_km=None if distance_km is None else round(distance_km, 1),
                score_breakdown=ScoreBreakdown(**{name: round(value) for name, value in components.items()}),
                reasons=_build_reasons(
                    provider,
                    budget=budget,
                    distance_km=distance_km,
                    requested_today=available_today,
                    is_available=available,
                    language=language,
                    rating_s=components["rating"],
                ),
            )
        )

    results.sort(
        key=lambda item: (
            -item.match_score,
            -item.provider.rating,
            item.provider.consultation_fee,
            item.provider.id,
        )
    )
    return results[:limit]
