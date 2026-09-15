"""Project-level domain models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class ProjectInfo:
    client: str
    project_name: str
    country: str
    city: str | None
    base_altitude_m: float
    currency: str
    seller: str | None
    quote_date: date
    notes: str | None = None
