"""Provider retrieval and filtering service (in-memory demo data).

Stage 3 uses a deterministic local dataset only — no database, no network.
All filters are combined with AND logic and are case-insensitive where
appropriate (city, area, specialization, language, days).
"""

from __future__ import annotations

from datetime import datetime

from app.data.providers import DEMO_PROVIDERS
from app.schemas.provider import Provider


def get_all_providers() -> list[Provider]:
    """Return every demo provider."""
    return list(DEMO_PROVIDERS)


def get_provider_by_id(provider_id: str) -> Provider | None:
    """Return a provider by exact id, or ``None`` if it does not exist."""
    wanted = provider_id.strip().casefold()
    return next((p for p in DEMO_PROVIDERS if p.id.casefold() == wanted), None)


def _text_matches(value: str, query: str | None) -> bool:
    """Case-insensitive substring match; empty/absent query matches everything."""
    if query is None or not query.strip():
        return True
    return query.strip().casefold() in value.casefold()


def _language_matches(provider: Provider, query: str | None) -> bool:
    if query is None or not query.strip():
        return True
    wanted = query.strip().casefold()
    return any(wanted in language.casefold() for language in provider.languages)


def search_providers(
    *,
    specialization: str | None = None,
    city: str | None = None,
    area: str | None = None,
    maximum_budget: float | None = None,
    minimum_rating: float | None = None,
    language: str | None = None,
    available_today: bool = False,
    today: str | None = None,
) -> list[Provider]:
    """Return providers matching ALL supplied filters (AND logic).

    Args:
        specialization: Case-insensitive specialization substring.
        city: Case-insensitive city substring.
        area: Case-insensitive locality substring.
        maximum_budget: Inclusive maximum consultation fee (INR).
        minimum_rating: Inclusive minimum rating (0-5).
        language: Case-insensitive language substring.
        available_today: If True, keep only providers available on ``today``.
        today: Weekday name used for the availability check; defaults to the
            current system weekday.
    """
    day_name = (today or datetime.now().strftime("%A")).strip().casefold()

    results: list[Provider] = []
    for provider in DEMO_PROVIDERS:
        if not _text_matches(provider.specialization, specialization):
            continue
        if not _text_matches(provider.city, city):
            continue
        if not _text_matches(provider.area, area):
            continue
        if maximum_budget is not None and provider.consultation_fee > maximum_budget:
            continue
        if minimum_rating is not None and provider.rating < minimum_rating:
            continue
        if not _language_matches(provider, language):
            continue
        if available_today and not any(d.casefold() == day_name for d in provider.available_days):
            continue
        results.append(provider)
    return results
