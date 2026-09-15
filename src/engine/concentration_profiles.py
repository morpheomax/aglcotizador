"""Design-concentration profile selection."""

from __future__ import annotations

import pandas as pd

from src.models.room import AgentType


def resolve_design_concentration(
    agent_type: AgentType,
    manual_concentration_pct: float,
    profile_id: str | None,
    profiles_df: pd.DataFrame | None,
) -> tuple[float, str, float | None, list[str]]:
    if not profile_id:
        return manual_concentration_pct, "Manual", None, []
    if profiles_df is None or profiles_df.empty:
        raise ValueError("No hay catálogo de perfiles de concentración cargado.")

    required_columns = {
        "profile_id",
        "agent_type",
        "profile_label",
        "design_concentration_pct",
        "occupied_max_pct",
        "requires_technical_review",
        "active",
    }
    if not required_columns.issubset(profiles_df.columns):
        raise ValueError("El catálogo de perfiles de concentración no contiene las columnas requeridas.")

    active = profiles_df[profiles_df["active"].map(_as_bool)]
    matches = active[active["profile_id"].astype(str) == profile_id]
    if matches.empty:
        raise ValueError("El perfil de concentración seleccionado no está disponible.")

    profile = matches.iloc[0]
    if str(profile["agent_type"]) != agent_type.value:
        raise ValueError("El perfil de concentración no corresponde al agente seleccionado.")

    warnings: list[str] = []
    if _as_bool(profile["requires_technical_review"]):
        warnings.append(
            f"El perfil {profile['profile_label']} requiere validación de Johnson Controls Technical Services."
        )

    return (
        float(profile["design_concentration_pct"]),
        str(profile["profile_label"]),
        float(profile["occupied_max_pct"]),
        warnings,
    )


def _as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "si", "sí"}
