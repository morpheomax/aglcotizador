"""System configuration domain models."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class SystemType(str, Enum):
    SYSTEM = "SISTEMA"
    MANIFOLD = "MANIFOLD"


class DischargeConnection(str, Enum):
    FLEXIBLE = "FLEXIBLE"
    HARDPIPE = "HARDPIPE"


@dataclass(frozen=True)
class SystemConfig:
    room_id: str
    system_type: SystemType = SystemType.SYSTEM
    discharge_connection: DischargeConnection = DischargeConnection.FLEXIBLE
    include_optional_items: bool = False
    include_reserve: bool = False
    include_main_reserve: bool = False
    force_cylinder: bool = False
    forced_cylinder_code: str | None = None
    forced_cylinder_qty: int | None = None
    override_nozzles: bool = False
    nozzle_qty_manual: int | None = None
    nozzle_override_reason: str | None = None
    manifold_nominal_diameter_dn: int | None = None
    reserve_sections_qty: int = 0
    custom_dead_volume_l: float = 0.0
