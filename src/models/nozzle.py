"""Nozzle calculation domain models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ProtectedAreaType(str, Enum):
    ROOM = "Sala principal"
    RAISED_FLOOR = "Piso técnico"
    FALSE_CEILING = "Cielo falso"


@dataclass(frozen=True)
class NozzleAreaResult:
    area_type: ProtectedAreaType
    area_m2: float
    coverage_m2: float
    minimum_qty: int


@dataclass(frozen=True)
class NozzleCalculationResult:
    areas: list[NozzleAreaResult]
    manufacturer_min_qty: int
    recommended_qty: int
    final_qty: int
    warnings: list[str] = field(default_factory=list)
    hydraulic_validation_required: bool = True
