"""LLM provider implementation — OpenAI-compatible chat completions.

The concrete vendor is decided entirely by configuration so the model can be
swapped later without touching parser or backend code:

    LLM_API_KEY   (required to enable the LLM path; no key => fallback parser)
    LLM_MODEL     (model name; sensible default when empty)
    LLM_BASE_URL  (any OpenAI-compatible endpoint; defaults to OpenAI's API)

Keys are read from arguments (backend settings) or environment variables —
never hardcoded, never returned to callers, never logged.
"""

from __future__ import annotations

import os

import httpx

from .base import LLMError, LLMProvider
from .prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE

DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_MODEL = "gpt-4o-mini"
TIMEOUT_SECONDS = 10.0


class OpenAICompatibleProvider(LLMProvider):
    """Minimal async chat-completions client (temperature 0 for determinism)."""

    def __init__(self, api_key: str, model: str, base_url: str | None = None) -> None:
        self._api_key = api_key
        self._model = model or DEFAULT_MODEL
        self._base_url = (base_url or DEFAULT_BASE_URL).rstrip("/")

    async def parse_healthcare_query(self, query: str) -> str:
        """Return the raw model output (JSON text) for one navigation query."""
        payload = {
            "model": self._model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": USER_PROMPT_TEMPLATE.format(query=query)},
            ],
        }
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
                response = await client.post(
                    f"{self._base_url}/chat/completions",
                    json=payload,
                    headers={"Authorization": f"Bearer {self._api_key}"},
                )
                response.raise_for_status()
                data = response.json()
            return data["choices"][0]["message"]["content"]
        except httpx.HTTPError as exc:
            # Exception messages must never contain the API key (header only).
            raise LLMError(f"LLM request failed ({type(exc).__name__})") from exc
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise LLMError("LLM returned an unexpected payload shape") from exc


def create_llm_provider(
    *,
    api_key: str | None = None,
    model: str | None = None,
    base_url: str | None = None,
) -> LLMProvider | None:
    """Return a provider from configuration, or ``None`` when no key is set.

    ``None`` is a first-class outcome: callers then use the deterministic
    fallback parser, so local development works with zero API keys.
    """
    key = (
        api_key if api_key is not None else os.environ.get("LLM_API_KEY", "")
    ).strip()
    if not key:
        return None
    resolved_model = (
        model if model is not None else os.environ.get("LLM_MODEL", "")
    ).strip()
    resolved_base = (
        base_url if base_url is not None else os.environ.get("LLM_BASE_URL", "")
    ).strip()
    return OpenAICompatibleProvider(
        api_key=key,
        model=resolved_model,
        base_url=resolved_base or None,
    )


__all__ = ["OpenAICompatibleProvider", "create_llm_provider"]
