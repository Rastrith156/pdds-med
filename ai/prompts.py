"""System prompt, guardrail messages and unsafe-intent patterns (Stage 7).

The system prompt constrains the model to navigation-parameter extraction
only. ``UNSAFE_PATTERNS`` provides a deterministic, model-independent safety
net: diagnosis/medication/treatment requests are refused BEFORE any LLM call
and never reach the recommendation engine.
"""

from __future__ import annotations

import re

SYSTEM_PROMPT = """You are a healthcare navigation query parser.

Your ONLY task is to extract search preferences from a user's natural-language request.

You do NOT diagnose diseases.
You do NOT recommend medicines.
You do NOT prescribe treatment.
You do NOT provide medical advice.
You do NOT determine what medical treatment a person needs.

You only convert a user's provider-search request into structured search parameters.

Respond with ONLY a single JSON object using exactly these keys, and null for
values the request does not mention:
specialization, city, area, maximum_budget, minimum_rating, language,
available_today, latitude, longitude.
No prose, no markdown fences, no additional keys."""

USER_PROMPT_TEMPLATE = "Extract the search parameters from this request: {query}"

# Refusal shown for diagnosis / medication / treatment requests.
SAFE_NAVIGATION_MESSAGE = (
    "I can help you find an appropriate healthcare provider, but I cannot "
    "diagnose conditions or recommend treatment. You can still search for a "
    "provider by specialization, location, budget or availability."
)

# Shown when no navigation criteria could be extracted from the request.
GUIDANCE_MESSAGE = (
    "I couldn't detect any search criteria. Please tell me the specialization, "
    "location, budget and availability you are looking for."
)

# Deterministic guardrail: any match => refuse (never sent to LLM or engine).
UNSAFE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bdiagnos\w*\b", re.IGNORECASE),
    re.compile(r"\bwhat\s+(?:disease|illness|medicine|drug|medication)\b", re.IGNORECASE),
    re.compile(r"\bshould\s+i\s+take\b", re.IGNORECASE),
    re.compile(r"\bprescrib\w*\b", re.IGNORECASE),
    re.compile(r"\bmedicines?\b", re.IGNORECASE),
    re.compile(r"\btreatment\b", re.IGNORECASE),
    re.compile(r"\bsymptoms?\b", re.IGNORECASE),
    re.compile(r"\bdo\s+i\s+have\b", re.IGNORECASE),
)

__all__ = [
    "GUIDANCE_MESSAGE",
    "SAFE_NAVIGATION_MESSAGE",
    "SYSTEM_PROMPT",
    "UNSAFE_PATTERNS",
    "USER_PROMPT_TEMPLATE",
]
