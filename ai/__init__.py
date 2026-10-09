"""MediAccess AI — natural-language healthcare-search parsing layer (Stage 7).

Framework-independent (no FastAPI imports): this package ONLY converts
free-text navigation requests into validated structured search parameters.

It never diagnoses, never prescribes, never provides medical advice, and
never ranks providers — ranking stays in the deterministic recommendation
engine (backend/app/services/recommendation_service.py).
"""

from .base import LLMError, LLMProvider, ParsedHealthcareQuery
from .fallback_parser import parse_fallback
from .parser import ParseOutcome, has_unsafe_intent, parse_query
from .provider import create_llm_provider

__all__ = [
    "LLMError",
    "LLMProvider",
    "ParsedHealthcareQuery",
    "ParseOutcome",
    "create_llm_provider",
    "has_unsafe_intent",
    "parse_fallback",
    "parse_query",
]
