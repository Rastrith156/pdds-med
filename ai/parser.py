"""Query parsing pipeline: safety guardrail -> LLM (if configured) -> fallback.

    user query
        |-- unsafe intent (diagnosis/medication/treatment) --> REFUSE (no LLM,
        |                                                      no engine call)
        |-- LLM available --> one request --> validate JSON via Pydantic
        |        |-- valid + criteria --> outcome(parser="llm")
        |        |-- any failure ------> fallback parser
        `-- no LLM --> deterministic fallback parser

The parser ONLY extracts search parameters. Ranking stays in the
deterministic recommendation engine; diagnosis/prescription never happens.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass

from .base import LLMProvider, ParsedHealthcareQuery
from .fallback_parser import parse_fallback
from .prompts import (
    GUIDANCE_MESSAGE,
    SAFE_NAVIGATION_MESSAGE,
    UNSAFE_PATTERNS,
)
from .provider import create_llm_provider

logger = logging.getLogger("medaccess.ai")

_FENCE_OPEN = re.compile(r"^```(?:json)?\s*", re.IGNORECASE)
_FENCE_CLOSE = re.compile(r"\s*```$")


def has_unsafe_intent(query: str) -> bool:
    """True when the query asks for diagnosis/medication/treatment.

    Deterministic regex guardrail that runs BEFORE any LLM call, so unsafe
    requests can never reach the model or the recommendation engine.
    """
    text = query or ""
    return any(pattern.search(text) for pattern in UNSAFE_PATTERNS)


@dataclass(frozen=True)
class ParseOutcome:
    """Result of parsing one query.

    ``parser``     — "llm" or "fallback" (which parser produced the result).
    ``parsed``     — validated parameters, or ``None`` when refused/guidance.
    ``refusal``    — safety message for diagnosis/medication requests.
    ``guidance``   — message when no search criteria could be extracted.
    """

    parser: str
    parsed: ParsedHealthcareQuery | None = None
    refusal: str | None = None
    guidance: str | None = None


def _validate_llm_output(raw: str) -> ParsedHealthcareQuery:
    """Parse raw model output into a validated ParsedHealthcareQuery.

    Tolerates markdown fences and surrounding prose, but the JSON itself must
    validate against the schema (``extra="forbid"`` rejects unexpected fields
    such as diagnosis/medication). Raises on anything invalid — callers fall
    back to the deterministic parser.
    """
    text = _FENCE_OPEN.sub("", (raw or "").strip())
    text = _FENCE_CLOSE.sub("", text.strip()).strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end < start:
        raise ValueError("LLM output contains no JSON object")
    return ParsedHealthcareQuery.model_validate(json.loads(text[start : end + 1]))


async def parse_query(
    query: str,
    *,
    provider: LLMProvider | None = None,
) -> ParseOutcome:
    """Parse one natural-language healthcare-navigation query.

    Args:
        query: raw user text (may be empty/whitespace).
        provider: an LLM provider to use; ``None`` means "create one from
            environment variables" (returns no provider when no key is set,
            which routes straight to the fallback parser).

    Returns:
        A :class:`ParseOutcome` carrying ``parser``, ``parsed`` and, when
        appropriate, a ``refusal`` or ``guidance`` message. Never raises for
        LLM problems — failures always degrade to the fallback parser.
    """
    text = (query or "").strip()

    if not text:
        return ParseOutcome(parser="fallback", guidance=GUIDANCE_MESSAGE)

    if has_unsafe_intent(text):
        # Refused before any LLM call; never reaches the engine.
        logger.info(
            "query refused by safety guardrail (len=%d, parser=fallback)", len(text)
        )
        return ParseOutcome(parser="fallback", refusal=SAFE_NAVIGATION_MESSAGE)

    active = provider if provider is not None else create_llm_provider()
    if active is not None:
        try:
            raw = await active.parse_healthcare_query(text)
            parsed = _validate_llm_output(raw)
            if parsed.has_criteria():
                logger.info("query parsed (parser=llm)")
                return ParseOutcome(parser="llm", parsed=parsed)
            # Valid JSON but nothing usable — let the fallback try too.
        except Exception as exc:  # noqa: BLE001 — any LLM failure => fallback
            logger.warning("LLM parse failed (%s); using fallback parser", type(exc).__name__)

    parsed = parse_fallback(text)
    if not parsed.has_criteria():
        logger.info("query parsed (parser=fallback, no criteria)")
        return ParseOutcome(parser="fallback", guidance=GUIDANCE_MESSAGE)
    logger.info("query parsed (parser=fallback)")
    return ParseOutcome(parser="fallback", parsed=parsed)


__all__ = ["ParseOutcome", "has_unsafe_intent", "parse_query"]
