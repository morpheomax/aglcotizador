"""Cylinder domain models."""

from __future__ import annotations

from dataclasses import dataclass, field

from src.models.room import AgentType


@dataclass(frozen=True)
class CylinderOption:
    agent_type: AgentType
    cylinder_label: str
    cylinder_code: str
    size_l: float
    min_fill_kg: float
    max_fill_kg: float
    valve_size_mm: int | None
    recommended_max_fill_pct: float = 85.0
    source: str | None = None


@dataclass(frozen=True)
class SelectedCylinder:
    room_id: str
    cylinder: CylinderOption
    quantity: int
    fill_per_cylinder_kg: float
    total_fill_kg: float
    excess_kg: float
    is_forced: bool = False
    warnings: list[str] = field(default_factory=list)
