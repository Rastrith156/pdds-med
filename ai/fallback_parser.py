"""Deterministic fallback parser — works with no LLM, key, or network.

Extracts ONLY navigation parameters (specialization, city, language, budget,
minimum rating, availability) via simple keyword/regex patterns. It never
invents values it cannot find: unmatched fields stay ``None``. Area and
coordinates are intentionally not guessed (the LLM path may supply them when
configured; a user can always use the structured search form).
"""

from __future__ import annotations

import re

from .base import ParsedHealthcareQuery

# (pattern, canonical value) — first match wins; order matters (specific first).
_SPECIALIZATIONS: tuple[tuple[str, str], ...] = (
    (r"\bdermatolog(?:ist|y)\b", "Dermatology"),
    (r"\bcardiolog(?:ist|y)\b", "Cardiology"),
    (r"\bneurolog(?:ist|y)\b", "Neurology"),
    (r"\bophthalmolog(?:ist|y)\b|\beye\s+doctor\b|\boptician\b", "Ophthalmology"),
    (r"\bgynecolog(?:ist|y)\b|\bgyneacolog\w*\b", "Gynecology"),
    (r"\bpediatric(?:ian|s)?\b|\bchildren'?s?\s+doctor\b", "Pediatrics"),
    (r"\borthoped(?:ic|ist|ics)\b|\bbone\s+(?:doctor|specialist|clinic)\b", "Orthopedics"),
    (r"\bdentist\b|\bdentistry\b|\bteeth\b", "Dentistry"),
    (r"\bent\b|\bear[,\s]+nose\b", "ENT"),
    (r"\bgeneral\s+med(?:icine)?\b|\bgeneral\s+practitioner\b|\bfamily\s+doctor\b|\bgp\b", "General Medicine"),
)

_CITIES: tuple[tuple[str, str], ...] = (
    (r"\bbangalore\b|\bbengaluru\b", "Bangalore"),
    (r"\bmysore\b|\bmysuru\b", "Mysore"),
    (r"\bmangalore\b|\bmangaluru\b", "Mangalore"),
    (r"\bchikkamagaluru\b|\bchikmagalur\b", "Chikkamagaluru"),
    (r"\bhassan\b", "Hassan"),
    (r"\bhubli\b|\bhubballi\b", "Hubli"),
    (r"\bbelagavi\b|\bbelgaum\b", "Belagavi"),
)

_LANGUAGES: tuple[tuple[str, str], ...] = (
    (r"\bkannada\b", "Kannada"),
    (r"\bhindi\b", "Hindi"),
    (r"\btamil\b", "Tamil"),
    (r"\bmalayalam\b", "Malayalam"),
    (r"\benglish\b", "English"),
)

# "under 700" / "under ₹700" / "within Rs. 1000" / "below 500 rupees" ...
_BUDGET = re.compile(
    r"(?:under|below|within|less\s+than|max(?:imum)?(?:\s+budget)?(?:\s+of)?)"
    r"\s*(?:₹|rs\.?|inr)?\s*(\d{1,6})",
    re.IGNORECASE,
)
# "rating above 4" / "rated 4.5 or higher" / "minimum rating of 4" ...
_RATING = re.compile(
    r"(?:rating|rated)\s*(?:above|over|greater\s+than|at\s+least|of|:)?"
    r"\s*(\d(?:\.\d+)?)",
    re.IGNORECASE,
)
_TODAY = re.compile(r"\b(?:today|right\s+now|available\s+now|asap)\b", re.IGNORECASE)


def _first_match(patterns: tuple[tuple[str, str], ...], text: str) -> str | None:
    for pattern, value in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return value
    return None


def _extract_budget(text: str) -> int | None:
    match = _BUDGET.search(text)
    return int(match.group(1)) if match else None


def _extract_rating(text: str) -> float | None:
    match = _RATING.search(text)
    return float(match.group(1)) if match else None


def parse_fallback(query: str) -> ParsedHealthcareQuery:
    """Extract navigation parameters from ``query`` deterministically.

    Returns a validated ``ParsedHealthcareQuery``; fields that cannot be
    detected remain ``None`` — missing information is never invented.
    """
    text = query or ""
    return ParsedHealthcareQuery(
        specialization=_first_match(_SPECIALIZATIONS, text),
        city=_first_match(_CITIES, text),
        area=None,
        maximum_budget=_extract_budget(text),
        minimum_rating=_extract_rating(text),
        language=_first_match(_LANGUAGES, text),
        available_today=bool(_TODAY.search(text)),
        latitude=None,
        longitude=None,
    )


__all__ = ["parse_fallback"]
