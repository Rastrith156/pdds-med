"""Pydantic schemas for healthcare provider records."""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator

WEEKDAYS: tuple[str, ...] = (
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
)

_SLOT_PATTERN = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


class Provider(BaseModel):
    """A healthcare provider record.

    All providers in this stage are fictional DEMO data (``is_demo=True``).
    This schema describes navigation metadata only — never medical advice.
    """

    id: str = Field(..., min_length=1, description="Unique provider identifier")
    name: str = Field(..., min_length=1, description="Provider display name")
    specialization: str = Field(..., min_length=1, description="Medical specialization")
    hospital: str = Field(..., min_length=1, description="Clinic or hospital name")
    city: str = Field(..., min_length=1, description="City")
    area: str = Field(..., min_length=1, description="Locality / neighbourhood")
    consultation_fee: float = Field(..., gt=0, description="Consultation fee in INR")
    rating: float = Field(..., ge=0, le=5, description="Average rating between 0 and 5")
    languages: list[str] = Field(..., min_length=1, description="Languages spoken")
    available_days: list[str] = Field(..., min_length=1, description="Available weekdays")
    available_slots: list[str] = Field(..., min_length=1, description="Available time slots (HH:MM)")
    latitude: float = Field(..., ge=-90, le=90, description="Approximate DEMO latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Approximate DEMO longitude")
    verified: bool = Field(..., description="Demo verification flag")
    is_demo: Literal[True] = Field(..., description="Always true: this is demo data")

    @field_validator("available_days")
    @classmethod
    def _validate_days(cls, value: list[str]) -> list[str]:
        normalized: list[str] = []
        for day in value:
            match = next((w for w in WEEKDAYS if w.casefold() == day.strip().casefold()), None)
            if match is None:
                raise ValueError(f"Invalid day '{day}'. Allowed: {', '.join(WEEKDAYS)}")
            if match not in normalized:
                normalized.append(match)
        return normalized

    @field_validator("available_slots")
    @classmethod
    def _validate_slots(cls, value: list[str]) -> list[str]:
        for slot in value:
            if not _SLOT_PATTERN.match(slot.strip()):
                raise ValueError(f"Invalid time slot '{slot}'. Expected format HH:MM (24h).")
        return value


class ProviderListResponse(BaseModel):
    """Response envelope for provider search results."""

    count: int = Field(..., description="Number of providers returned")
    providers: list[Provider] = Field(..., description="Matching demo providers")


__all__ = ["Provider", "ProviderListResponse", "WEEKDAYS"]
