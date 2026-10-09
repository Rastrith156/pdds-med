"""Regression and unit tests for the AI parsing layer (Stage 7).

Fully offline: no LLM key, no network, no server. Locks down the deterministic
fallback parser (including the city case-insensitivity regression), the
unsafe-intent guardrail, and parse_query's routing behaviour.
"""

from __future__ import annotations

import asyncio

from ai.base import LLMError, LLMProvider
from ai.fallback_parser import parse_fallback
from ai.parser import has_unsafe_intent, parse_query
from ai.prompts import GUIDANCE_MESSAGE, SAFE_NAVIGATION_MESSAGE


class _FailingProvider(LLMProvider):
    """Always fails — proves parse_query degrades to the fallback parser."""

    def __init__(self) -> None:
        self.calls = 0

    async def parse_healthcare_query(self, query: str) -> str:
        self.calls += 1
        raise LLMError("offline test provider")


class _GoodProvider(LLMProvider):
    """Returns valid fenced JSON — proves the LLM path validates output."""

    async def parse_healthcare_query(self, query: str) -> str:
        return '```json\n{"specialization": "Neurology", "city": "Mysore"}\n```'


# ------------------------------------------------------------- fallback parser

def test_canonical_query_parses_all_criteria() -> None:
    parsed = parse_fallback("I need a dermatologist near Bangalore under 700 rupees today.")
    assert parsed.specialization == "Dermatology"
    assert parsed.city == "Bangalore"
    assert parsed.maximum_budget == 700
    assert parsed.available_today is True
    assert parsed.has_criteria()


def test_city_matching_is_case_insensitive() -> None:
    # Regression: _first_match originally omitted re.IGNORECASE, so a
    # capitalized "Bangalore" never matched the lowercase pattern.
    for text in ("I need a doctor in Bangalore", "doctor in BANGALORE", "doctor in bengaluru"):
        assert parse_fallback(text).city == "Bangalore", text


def test_city_synonyms_map_to_canonical_values() -> None:
    cases = {
        "clinic in mysuru": "Mysore",
        "clinic in mangaluru": "Mangalore",
        "clinic in chikmagalur": "Chikkamagaluru",
        "clinic in hassan": "Hassan",
        "clinic in hubballi": "Hubli",
        "clinic in belgaum": "Belagavi",
    }
    for text, expected in cases.items():
        assert parse_fallback(text).city == expected, text


def test_specialization_variants_map_to_canonical_values() -> None:
    cases = {
        "see a dermatologist": "Dermatology",
        "book cardiology consultation": "Cardiology",
        "see a neurologist": "Neurology",
        "visit an eye doctor": "Ophthalmology",
        "need a gynecologist": "Gynecology",
        "need a pediatrician": "Pediatrics",
        "see an orthopedic doctor": "Orthopedics",
        "see a dentist": "Dentistry",
        "see an ENT specialist": "ENT",
        "see a general practitioner": "General Medicine",
    }
    for text, expected in cases.items():
        assert parse_fallback(text).specialization == expected, text


def test_budget_patterns() -> None:
    cases = {
        "under ₹700": 700,
        "below 500 rupees": 500,
        "within Rs. 1000": 1000,
        "maximum budget of 800": 800,
    }
    for text, expected in cases.items():
        assert parse_fallback(text).maximum_budget == expected, text


def test_rating_patterns() -> None:
    assert parse_fallback("rated 4.5 or higher").minimum_rating == 4.5
    assert parse_fallback("rating above 4").minimum_rating == 4.0


def test_language_and_availability_extraction() -> None:
    assert parse_fallback("kannada speaking doctor please").language == "Kannada"
    assert parse_fallback("I want a Hindi speaking doctor").language == "Hindi"
    assert parse_fallback("see someone today").available_today is True
    assert parse_fallback("available asap").available_today is True
    assert parse_fallback("appointment tomorrow").available_today is False


def test_no_values_are_invented_for_vague_queries() -> None:
    parsed = parse_fallback("hello there friend")
    assert parsed.has_criteria() is False
    assert parsed.specialization is None
    assert parsed.city is None
    assert parsed.maximum_budget is None
    assert parsed.language is None
    assert parsed.available_today is False


# ------------------------------------------------------------------ guardrail

def test_unsafe_intent_guardrail_detects_diagnosis_requests() -> None:
    unsafe = [
        "Do I have diabetes?",
        "What medicine should I take for fever?",
        "Please diagnose my skin rash",
        "prescribe something for my headache",
        "what are the symptoms of flu",
        "suggest a treatment for my injury",
    ]
    for text in unsafe:
        assert has_unsafe_intent(text), text


def test_safe_navigation_queries_are_not_flagged() -> None:
    safe = [
        "I need a dermatologist near Bangalore under 700 today",
        "find a general physician in Mysore",
        "show me pediatricians in Mangalore rated above 4",
    ]
    for text in safe:
        assert not has_unsafe_intent(text), text


# -------------------------------------------------------------- parse routing

def test_unsafe_query_refused_before_any_llm_call() -> None:
    provider = _FailingProvider()
    outcome = asyncio.run(parse_query("Do I have diabetes?", provider=provider))
    assert outcome.refusal == SAFE_NAVIGATION_MESSAGE
    assert outcome.parsed is None
    assert provider.calls == 0  # guardrail runs before the model


def test_llm_failure_falls_back_to_deterministic_parser() -> None:
    provider = _FailingProvider()
    outcome = asyncio.run(
        parse_query("I need a dermatologist in Bangalore under 700 today", provider=provider)
    )
    assert outcome.parser == "fallback"
    assert provider.calls == 1
    assert outcome.parsed is not None
    assert outcome.parsed.specialization == "Dermatology"
    assert outcome.parsed.city == "Bangalore"


def test_valid_llm_output_is_used() -> None:
    outcome = asyncio.run(parse_query("find me someone", provider=_GoodProvider()))
    assert outcome.parser == "llm"
    assert outcome.parsed is not None
    assert outcome.parsed.specialization == "Neurology"
    assert outcome.parsed.city == "Mysore"


def test_empty_and_unparseable_queries_return_guidance() -> None:
    empty = asyncio.run(parse_query("   "))
    assert empty.guidance == GUIDANCE_MESSAGE
    assert empty.parsed is None
    vague = asyncio.run(parse_query("hello there friend", provider=_FailingProvider()))
    assert vague.guidance == GUIDANCE_MESSAGE
    assert vague.parsed is None
