"""Nozzle quantity calculations."""

from __future__ import annotations

from math import ceil

import pandas as pd

from src.models.nozzle import NozzleAreaResult, NozzleCalculationResult, ProtectedAreaType
from src.models.room import AgentType, RoomInput
from src.models.system_config import SystemConfig


def calculate_min_nozzles(area_m2: float, coverage_m2: float) -> int:
    if area_m2 <= 0:
        raise ValueError("El área debe ser mayor que cero.")
    if coverage_m2 <= 0:
        raise ValueError("La cobertura por boquilla debe ser mayor que cero.")
    return max(1, ceil(area_m2 / coverage_m2))


def get_nozzle_coverage(agent_type: AgentType, catalog_df: pd.DataFrame) -> tuple[float, int]:
    if catalog_df.empty:
        raise ValueError("No hay catálogo de cobertura de boquillas cargado.")
    rows = catalog_df[catalog_df["agent_type"] == agent_type.value].copy()
    if "active" in rows.columns:
        rows = rows[rows["active"].map(lambda value: str(value).strip().lower() in {"1", "true", "yes", "si", "sí"})]
    if rows.empty:
        raise ValueError("No hay cobertura de boquillas activa para el agente seleccionado.")
    row = rows.iloc[0]
    return float(row["coverage_m2"]), int(row["max_nozzles"])


def calculate_room_nozzles(
    room: RoomInput,
    config: SystemConfig,
    coverage_m2: float,
    max_nozzles: int = 20,
) -> NozzleCalculationResult:
    area_m2 = room.length_m * room.width_m
    protected_areas = [ProtectedAreaType.ROOM]
    if room.protect_raised_floor and room.raised_floor_m > 0:
        protected_areas.append(ProtectedAreaType.RAISED_FLOOR)
    if room.protect_false_ceiling and room.false_ceiling_m > 0:
        protected_areas.append(ProtectedAreaType.FALSE_CEILING)

    areas = [
        NozzleAreaResult(area_type, area_m2, coverage_m2, calculate_min_nozzles(area_m2, coverage_m2))
        for area_type in protected_areas
    ]
    manufacturer_min = sum(area.minimum_qty for area in areas)
    exactly_three_single_areas = len(areas) == 3 and all(area.minimum_qty == 1 for area in areas)
    recommended = manufacturer_min if manufacturer_min % 2 == 0 or exactly_three_single_areas else manufacturer_min + 1
    final_qty = recommended
    warnings: list[str] = []

    if config.override_nozzles:
        if config.nozzle_qty_manual is None:
            raise ValueError("Debe ingresar la cantidad manual de boquillas.")
        if config.nozzle_qty_manual < manufacturer_min:
            raise ValueError("La cantidad manual de boquillas es menor al mínimo técnico calculado.")
        if config.nozzle_qty_manual % 2 != 0 and not exactly_three_single_areas:
            if not (config.nozzle_override_reason or "").strip():
                raise ValueError("Una cantidad impar de boquillas requiere una justificación técnica.")
            warnings.append("Se usó una cantidad impar de boquillas con justificación técnica.")
        final_qty = config.nozzle_qty_manual

    if final_qty > max_nozzles:
        warnings.append(
            f"La cantidad de boquillas supera el máximo preliminar de {max_nozzles} por recinto; "
            "se requiere dividir el sistema o revisión de ingeniería."
        )

    warnings.append(
        "El tiempo de descarga de 6 a 10 s, presión, caudal y orificios requieren validación hidráulica certificada."
    )
    return NozzleCalculationResult(areas, manufacturer_min, recommended, final_qty, warnings)
