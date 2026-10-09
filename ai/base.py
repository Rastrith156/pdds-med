"""Abstract LLM provider interface and the structured search schema."""

from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import BaseModel, ConfigDict, Field, model_validator


class LLMError(Exception):
    """Raised when the LLM provider fails (timeout, HTTP error, bad payload).

    Messages must never contain API keys or raw provider responses.
    """


class LLMProvider(ABC):
    """Vendor-agnostic LLM interface.

    Swap implementations later without touching the parser or the backend —
    configuration (key/model/base URL) comes from environment variables only.
    """

    @abstractmethod
    async def parse_healthcare_query(self, query: str) -> str:
        """Return the raw model output (JSON text) for one navigation query."""


class ParsedHealthcareQuery(BaseModel):
    """The ONLY parameters the parser may extract from a user query.

    ``extra="forbid"`` rejects any unexpected field (diagnosis, medication,
    treatment, ...), so raw LLM JSON is never trusted as-is. Values are then
    range-validated by the same rules the recommendation request uses.
    """

    model_config = ConfigDict(extra="forbid")

    specialization: str | None = Field(None, examples=["Dermatology"], description="Provider specialization")
    city: str | None = Field(None, examples=["Bangalore"], description="City")
    area: str | None = Field(None, examples=["Indiranagar"], description="Locality within the city")
    maximum_budget: int | None = Field(None, gt=0, examples=[700], description="Maximum consultation fee in INR")
    minimum_rating: float | None = Field(None, ge=0, le=5, examples=[4.0], description="Minimum rating (0-5)")
    language: str | None = Field(None, examples=["Kannada"], description="Preferred language spoken")
    available_today: bool = Field(False, description="Available on the current weekday")
    latitude: float | None = Field(None, ge=-90, le=90, description="User latitude")
    longitude: float | None = Field(None, ge=-180, le=180, description="User longitude")

    @model_validator(mode="after")
    def _require_paired_coordinates(self) -> ParsedHealthcareQuery:
        """Location must be supplied as both latitude AND longitude, or neither."""
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("Both latitude and longitude must be supplied together.")
        return self

    def has_criteria(self) -> bool:
        """True when at least one usable navigation criterion was extracted."""
        return bool(
            (self.specialization and self.specialization.strip())
            or (self.city and self.city.strip())
            or (self.area and self.area.strip())
            or (self.language and self.language.strip())
            or self.maximum_budget is not None
            or self.minimum_rating is not None
            or self.available_today
            or self.latitude is not None
        )


__all__ = ["LLMError", "LLMProvider", "ParsedHealthcareQuery"]
