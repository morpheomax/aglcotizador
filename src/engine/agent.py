"""Agent quantity calculations."""

from __future__ import annotations

from math import ceil

import pandas as pd

from src.models.room import AgentType


_AGENT_PROPERTIES: dict[AgentType, tuple[float, float, float, float, float, float]] = {
    # Specific-volume intercept/coefficient, temperature limits, and concentration limits.
    AgentType.FM200: (0.1269, 0.0005131, -10.0, 55.0, 6.4, 15.0),
    AgentType.FK5112: (0.0664, 0.000274, -20.0, 65.0, 4.0, 10.0),
}


def get_flooding_factor(
    agent_type: AgentType,
    concentration_pct: float,
    min_temp_c: float,
    flooding_factors_df: pd.DataFrame,
) -> float:
    if flooding_factors_df.empty:
        raise ValueError("No hay catálogo de flooding factors cargado.")

    if "agent_type" not in flooding_factors_df.columns or agent_type.value not in set(
        flooding_factors_df["agent_type"].astype(str)
    ):
        raise ValueError("No hay datos de flooding factor para el agente seleccionado.")

    intercept, coefficient, min_temp, max_temp, min_concentration, max_concentration = _AGENT_PROPERTIES[agent_type]
    if not min_temp <= min_temp_c <= max_temp:
        raise ValueError(
            f"La temperatura está fuera del rango publicado para {agent_type.value}: "
            f"{min_temp:g} °C a {max_temp:g} °C."
        )
    if not min_concentration <= concentration_pct <= max_concentration:
        raise ValueError(
            f"La concentración está fuera del rango publicado para {agent_type.value}: "
            f"{min_concentration:g}% a {max_concentration:g}%."
        )

    specific_vapor_volume = intercept + coefficient * min_temp_c
    return (concentration_pct / (100.0 - concentration_pct)) / specific_vapor_volume


def calculate_required_agent(net_volume_m3: float, flooding_factor: float, altitude_factor: float) -> float:
    if net_volume_m3 <= 0:
        raise ValueError("El volumen neto debe ser mayor que cero.")
    if flooding_factor <= 0:
        raise ValueError("El flooding factor debe ser mayor que cero.")
    if altitude_factor <= 0:
        raise ValueError("El factor de altitud debe ser mayor que cero.")
    return net_volume_m3 * flooding_factor * altitude_factor


def calculate_achieved_concentration(
    agent_kg: float,
    net_volume_m3: float,
    agent_type: AgentType,
    temperature_c: float,
    altitude_factor: float,
) -> float:
    if agent_kg <= 0:
        raise ValueError("El agente calculado debe ser mayor que cero.")
    if net_volume_m3 <= 0:
        raise ValueError("El volumen neto debe ser mayor que cero.")
    if altitude_factor <= 0:
        raise ValueError("El factor de altitud debe ser mayor que cero.")

    intercept, coefficient, min_temp, max_temp, _, _ = _AGENT_PROPERTIES[agent_type]
    if not min_temp <= temperature_c <= max_temp:
        raise ValueError(
            f"La temperatura está fuera del rango publicado para {agent_type.value}: "
            f"{min_temp:g} °C a {max_temp:g} °C."
        )

    specific_vapor_volume = intercept + coefficient * temperature_c
    return 100.0 * agent_kg * specific_vapor_volume / (
        net_volume_m3 * altitude_factor + agent_kg * specific_vapor_volume
    )


def round_agent_quantity(agent_kg: float, increment_kg: float = 1.0) -> float:
    if agent_kg <= 0:
        raise ValueError("El agente calculado debe ser mayor que cero.")
    if increment_kg <= 0:
        raise ValueError("El incremento de redondeo debe ser mayor que cero.")
    return ceil(agent_kg / increment_kg) * increment_kg
