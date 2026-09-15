"""Agent allowance for manifold and pipe dead volume."""

from __future__ import annotations

import pandas as pd

from src.models.room import AgentType


_LIQUID_DENSITY_KG_M3 = {
    AgentType.FM200: 1410.0,
    AgentType.FK5112: 1600.0,
}


def calculate_dead_volume_l(
    nominal_diameter_dn: int | None,
    reserve_sections_qty: int,
    custom_dead_volume_l: float,
    dead_volume_factors_df: pd.DataFrame | None,
) -> float:
    if reserve_sections_qty < 0:
        raise ValueError("La cantidad de secciones de reserva no puede ser negativa.")
    if custom_dead_volume_l < 0:
        raise ValueError("El volumen muerto adicional no puede ser negativo.")
    if nominal_diameter_dn is None:
        if reserve_sections_qty:
            raise ValueError("Debe seleccionar un diámetro de manifold para agregar secciones de reserva.")
        return custom_dead_volume_l
    if dead_volume_factors_df is None or dead_volume_factors_df.empty:
        raise ValueError("No hay catálogo de volumen muerto cargado.")

    required_columns = {"nominal_diameter_dn", "dead_end_volume_l", "reserve_section_volume_l"}
    if not required_columns.issubset(dead_volume_factors_df.columns):
        raise ValueError("El catálogo de volumen muerto no contiene las columnas requeridas.")

    matches = dead_volume_factors_df[
        dead_volume_factors_df["nominal_diameter_dn"].astype(int) == nominal_diameter_dn
    ]
    if matches.empty:
        raise ValueError("El diámetro de manifold no está publicado en la Tabla 5-8.")

    row = matches.iloc[0]
    return (
        float(row["dead_end_volume_l"])
        + reserve_sections_qty * float(row["reserve_section_volume_l"])
        + custom_dead_volume_l
    )


def calculate_pipe_agent_allowance(agent_type: AgentType, dead_volume_l: float) -> float:
    if dead_volume_l < 0:
        raise ValueError("El volumen muerto no puede ser negativo.")
    return dead_volume_l / 1000.0 * _LIQUID_DENSITY_KG_M3[agent_type]
