"""BOM domain models."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from src.models.room import AgentType


class BomType(str, Enum):
    SYSTEM = "SISTEMA"
    OPTIONAL = "OPCIONAL"
    RESERVE = "RESERVA"
    MAIN_RESERVE = "MAIN RESERVE"
    MANIFOLD = "MANIFOLD"
    AGENT = "AGENTE"
    CYLINDER = "CILINDRO"


@dataclass(frozen=True)
class BomCatalogItem:
    item_id: str | int
    key: str | None
    enabled: bool
    bom_type: str
    cylinder_label: str | None
    agent_type: AgentType | None
    item_order: int | None
    brand: str | None
    code: str
    product: str
    unit: str
    quantity_base: float
    delivery: str | None
    unit_price: float | None


@dataclass(frozen=True)
class BomLine:
    project_id: str | None
    room_id: str
    room_name: str
    system_type: str
    bom_type: str
    agent_type: AgentType
    cylinder_label: str | None
    brand: str | None
    code: str
    product: str
    unit: str
    quantity: float
    unit_price: float | None
    total_price: float | None
    delivery: str | None
    selected: bool = True
    notes: str | None = None
