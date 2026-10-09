"""Provider retrieval and filtering service (Stage 5: MongoDB-backed).

Architecture: router -> provider service -> database -> MongoDB.

Two explicit modes (see ``app.database``):
- ``mongodb``: filters are executed INSIDE MongoDB as a single query with AND
  logic (no fetching the whole collection into memory). Case-insensitive
  substring semantics from Stage 3 are preserved with unanchored,
  case-insensitive regexes.
- ``memory``: identical semantics evaluated in Python over the demo dataset —
  used ONLY by unit tests so they stay independent of the database.

If MongoDB is required but unreachable, :class:`DatabaseUnavailableError` is
raised so routers can return HTTP 503 instead of fabricating results.
"""

from __future__ import annotations

import re
from datetime import datetime

from pymongo.errors import PyMongoError

from app import database
from app.data.providers import DEMO_PROVIDERS
from app.schemas.provider import Provider


def _escape(value: str) -> str:
    """Regex-escape user input and trim it (safe literal matching)."""
    return re.escape(value.strip())


def _text_regex(value: str) -> dict:
    """Unanchored, case-insensitive regex for substring filters (Stage 3 parity)."""
    return {"$regex": _escape(value), "$options": "i"}


async def get_all_providers() -> list[Provider]:
    """Return every provider (memory: dataset; mongodb: full collection)."""
    if database.is_memory_mode():
        return list(DEMO_PROVIDERS)
    try:
        docs = database.get_providers_collection().find({})
        return [Provider.model_validate(doc) async for doc in docs]
    except PyMongoError as exc:
        raise database.DatabaseUnavailableError(_DB_DOWN) from exc


async def get_provider_by_id(provider_id: str) -> Provider | None:
    """Return a provider by id (case-insensitive), or ``None`` if unknown."""
    if database.is_memory_mode():
        wanted = provider_id.strip().casefold()
        return next((p for p in DEMO_PROVIDERS if p.id.casefold() == wanted), None)
    try:
        doc = await database.get_providers_collection().find_one(
            {"id": {"$regex": f"^{re.escape(provider_id.strip())}$", "$options": "i"}}
        )
    except PyMongoError as exc:
        raise database.DatabaseUnavailableError(_DB_DOWN) from exc
    return Provider.model_validate(doc) if doc else None


_DB_DOWN = (
    "MongoDB is unreachable. Provider data cannot be served without the "
    "database — start it with 'docker compose up -d mongodb'."
)


# ----------------------------------------------------------- memory (unit tests)

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


def _memory_search(
    *,
    specialization: str | None,
    city: str | None,
    area: str | None,
    maximum_budget: float | None,
    minimum_rating: float | None,
    language: str | None,
    available_today: bool,
    today: str | None,
) -> list[Provider]:
    """Stage 3 in-memory filtering (identical semantics to the Mongo query)."""
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


# ------------------------------------------------------------------ mongodb

def _build_mongo_filter(
    *,
    specialization: str | None,
    city: str | None,
    area: str | None,
    maximum_budget: float | None,
    minimum_rating: float | None,
    language: str | None,
    available_today: bool,
    today: str | None,
) -> dict:
    """Translate Stage 3 filter semantics into ONE MongoDB query (AND logic).

    Text filters become unanchored case-insensitive regexes (substring,
    case-insensitive); budget/rating become $lte/$gte; language matches any
    array element; availability matches the exact weekday, case-insensitive.
    """
    query: dict = {}
    if specialization and specialization.strip():
        query["specialization"] = _text_regex(specialization)
    if city and city.strip():
        query["city"] = _text_regex(city)
    if area and area.strip():
        query["area"] = _text_regex(area)
    if maximum_budget is not None:
        query["consultation_fee"] = {"$lte": maximum_budget}
    if minimum_rating is not None:
        query["rating"] = {"$gte": minimum_rating}
    if language and language.strip():
        query["languages"] = _text_regex(language)
    if available_today:
        day_name = (today or datetime.now().strftime("%A")).strip()
        query["available_days"] = {"$regex": f"^{re.escape(day_name)}$", "$options": "i"}
    return query


async def search_providers(
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

    In mongodb mode the filtering happens inside MongoDB (a single indexed
    query — the collection is not loaded into memory). In memory mode the
    same logic runs over the demo dataset. Raises DatabaseUnavailableError
    when mongodb mode is configured but the database cannot be reached.
    """
    if database.is_memory_mode():
        return _memory_search(
            specialization=specialization,
            city=city,
            area=area,
            maximum_budget=maximum_budget,
            minimum_rating=minimum_rating,
            language=language,
            available_today=available_today,
            today=today,
        )
    query = _build_mongo_filter(
        specialization=specialization,
        city=city,
        area=area,
        maximum_budget=maximum_budget,
        minimum_rating=minimum_rating,
        language=language,
        available_today=available_today,
        today=today,
    )
    try:
        docs = database.get_providers_collection().find(query)
        return [Provider.model_validate(doc) async for doc in docs]
    except PyMongoError as exc:
        raise database.DatabaseUnavailableError(_DB_DOWN) from exc
