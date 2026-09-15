"""Room domain models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class AgentType(str, Enum):
    FM200 = "FM-200"
    FK5112 = "FK-5-1-12"


@dataclass(frozen=True)
class RoomInput:
    room_id: str
    name: str
    agent_type: AgentType
    length_m: float
    width_m: float
    height_m: float
    raised_floor_m: float = 0.0
    false_ceiling_m: float = 0.0
    structural_reductions_m3: float = 0.0
    object_reductions_m3: float = 0.0
    min_temp_c: float = 18.0
    max_temp_c: float = 27.0
    normal_temp_c: float = 21.0
    design_concentration_pct: float = 7.0
    altitude_m: float = 0.0
    notes: str | None = None
    protect_raised_floor: bool = False
    protect_false_ceiling: bool = False
    concentration_profile_id: str | None = None
    object_reductions_are_permanent: bool = True


@dataclass(frozen=True)
class RoomCalculationResult:
    room_id: str
    area_m2: float
    volume_room_m3: float
    volume_raised_floor_m3: float
    volume_false_ceiling_m3: float
    gross_volume_m3: float
    net_volume_m3: float
    flooding_factor: float
    altitude_factor: float
    agent_required_exact_kg: float
    agent_required_rounded_kg: float
    nozzle_min_qty: int
    minimum_concentration_achieved_pct: float = 0.0
    maximum_concentration_achieved_pct: float = 0.0
    nozzle_recommended_qty: int = 0
    nozzle_final_qty: int = 0
    nozzle_area_summary: str = ""
    hydraulic_validation_required: bool = True
    warnings: list[str] = field(default_factory=list)
    concentration_profile_label: str = "Manual"
    design_concentration_applied_pct: float = 0.0
    occupied_max_concentration_pct: float | None = None
    enclosure_agent_required_exact_kg: float = 0.0
    pipe_dead_volume_l: float = 0.0
    pipe_agent_allowance_kg: float = 0.0
    agent_available_to_enclosure_kg: float = 0.0
