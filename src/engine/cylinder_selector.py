"""Preliminary cylinder selection engine."""

from __future__ import annotations

import pandas as pd

from src.models.cylinder import CylinderOption, SelectedCylinder
from src.models.room import AgentType
from src.models.system_config import SystemType


def _row_to_cylinder(row: pd.Series) -> CylinderOption:
    valve = row.get("valve_size_mm")
    valve_size_mm = None if pd.isna(valve) else int(valve)
    return CylinderOption(
        agent_type=AgentType(str(row["agent_type"])),
        cylinder_label=str(row["cylinder_label"]),
        cylinder_code=str(row["cylinder_code"]),
        size_l=float(row["size_l"]),
        min_fill_kg=float(row["min_fill_kg"]),
        max_fill_kg=float(row["max_fill_kg"]),
        valve_size_mm=valve_size_mm,
        recommended_max_fill_pct=_recommended_max_fill_pct(row),
        source=None if pd.isna(row.get("source")) else str(row.get("source")),
    )


def select_cylinder(
    room_id: str,
    agent_required_kg: float,
    agent_type: AgentType,
    system_type: SystemType,
    catalog_df: pd.DataFrame,
    forced_cylinder_code: str | None = None,
    forced_cylinder_qty: int | None = None,
    max_cylinders: int = 100,
) -> SelectedCylinder:
    if catalog_df.empty:
        raise ValueError("No hay catálogo de cilindros cargado.")
    if agent_required_kg <= 0:
        raise ValueError("El agente requerido debe ser mayor que cero.")

    df = catalog_df[catalog_df["agent_type"] == agent_type.value].copy()
    if "active" in df.columns:
        df = df[df["active"].map(_as_bool)]
    if df.empty:
        raise ValueError("No hay cilindros activos para el agente seleccionado.")

    if forced_cylinder_code:
        return validate_forced_cylinder(
            room_id=room_id,
            agent_required_kg=agent_required_kg,
            agent_type=agent_type,
            catalog_df=df,
            forced_cylinder_code=forced_cylinder_code,
            forced_cylinder_qty=forced_cylinder_qty,
        )

    min_quantity = 2 if system_type == SystemType.MANIFOLD else 1
    selected = _select_equal_cylinders(room_id, agent_required_kg, agent_type, df, min_quantity, max_cylinders)
    if system_type == SystemType.MANIFOLD and selected.quantity < 2:
        return _with_added_warning(
            selected,
            "Se solicitó MANIFOLD, pero el preselector encontró una configuración simple. Revise la configuración.",
        )
    return selected


def _select_single(room_id: str, agent_required_kg: float, catalog_df: pd.DataFrame) -> SelectedCylinder:
    valid = catalog_df[
        (catalog_df["min_fill_kg"].astype(float) <= agent_required_kg)
        & (catalog_df["max_fill_kg"].astype(float) >= agent_required_kg)
    ].copy()
    if valid.empty:
        raise ValueError("No se encontró cilindro simple compatible con el agente requerido.")
    valid["excess_kg"] = valid["max_fill_kg"].astype(float) - agent_required_kg
    selected_row = valid.sort_values(["excess_kg", "size_l"]).iloc[0]
    cylinder = _row_to_cylinder(selected_row)
    return SelectedCylinder(
        room_id=room_id,
        cylinder=cylinder,
        quantity=1,
        fill_per_cylinder_kg=agent_required_kg,
        total_fill_kg=agent_required_kg,
        excess_kg=float(selected_row["excess_kg"]),
    )


def _select_equal_cylinders(
    room_id: str,
    agent_required_kg: float,
    agent_type: AgentType,
    catalog_df: pd.DataFrame,
    min_quantity: int,
    max_cylinders: int,
) -> SelectedCylinder:
    candidates = _build_candidate_tuples(agent_required_kg, catalog_df, min_quantity, max_cylinders)

    if candidates:
        excess, quantity, fill_per_cylinder, row = _choose_best_candidate(candidates, min_quantity)
        return _candidate_to_selection(room_id, agent_required_kg, min_quantity, excess, quantity, fill_per_cylinder, row)

    raise ValueError(
        "No se encontró una combinación de cilindros dentro del rango mínimo/máximo "
        f"de llenado y el límite de {max_cylinders} cilindros."
    )


def list_valid_cylinder_selections(
    room_id: str,
    agent_required_kg: float,
    agent_type: AgentType,
    system_type: SystemType,
    catalog_df: pd.DataFrame,
    max_cylinders: int = 100,
) -> list[SelectedCylinder]:
    if catalog_df.empty:
        raise ValueError("No hay catálogo de cilindros cargado.")
    if agent_required_kg <= 0:
        raise ValueError("El agente requerido debe ser mayor que cero.")

    rows = catalog_df[catalog_df["agent_type"] == agent_type.value].copy()
    if "active" in rows.columns:
        rows = rows[rows["active"].map(_as_bool)]
    if rows.empty:
        return []

    min_quantity = 2 if system_type == SystemType.MANIFOLD else 1
    candidates = _build_candidate_tuples(agent_required_kg, rows, min_quantity, max_cylinders)
    selections = [
        _candidate_to_selection(
            room_id,
            agent_required_kg,
            min_quantity,
            excess,
            quantity,
            fill_per_cylinder,
            row,
        )
        for _, quantity, excess, fill_per_cylinder, row in candidates
    ]
    selections = sorted(
        selections,
        key=lambda item: (
            item.quantity,
            item.fill_per_cylinder_kg / item.cylinder.max_fill_kg > item.cylinder.recommended_max_fill_pct / 100,
            item.excess_kg,
            item.cylinder.size_l,
        ),
    )
    _, recommended_quantity, _, recommended_row = _choose_best_candidate(candidates, min_quantity)
    recommended_code = str(recommended_row["cylinder_code"])
    return sorted(
        selections,
        key=lambda item: 0
        if item.quantity == recommended_quantity and item.cylinder.cylinder_code == recommended_code
        else 1,
    )


def _build_candidate_tuples(
    agent_required_kg: float,
    catalog_df: pd.DataFrame,
    min_quantity: int,
    max_cylinders: int,
) -> list[tuple[bool, int, float, float, pd.Series]]:
    candidates: list[tuple[bool, int, float, float, pd.Series]] = []
    for _, row in catalog_df.iterrows():
        for quantity in range(min_quantity, max_cylinders + 1):
            fill_per_cylinder = agent_required_kg / quantity
            min_fill = float(row["min_fill_kg"])
            max_fill = float(row["max_fill_kg"])
            if min_fill <= fill_per_cylinder <= max_fill:
                excess = (max_fill * quantity) - agent_required_kg
                recommended_max_pct = _recommended_max_fill_pct(row)
                fill_pct = (fill_per_cylinder / max_fill) * 100
                exceeds_recommended = fill_pct > _recommended_limit_with_tolerance(recommended_max_pct)
                candidates.append((exceeds_recommended, quantity, excess, fill_per_cylinder, row))
    return candidates


def _candidate_to_selection(
    room_id: str,
    agent_required_kg: float,
    min_quantity: int,
    excess: float,
    quantity: int,
    fill_per_cylinder: float,
    row: pd.Series,
) -> SelectedCylinder:
    cylinder = _row_to_cylinder(row)
    fill_pct = (fill_per_cylinder / cylinder.max_fill_kg) * 100
    warnings = _selection_warnings(quantity, min_quantity)
    if fill_pct > cylinder.recommended_max_fill_pct:
        warnings.append("El llenado queda sobre el margen recomendado de presurización; revise el tamaño de cilindro.")
    return SelectedCylinder(
        room_id=room_id,
        cylinder=cylinder,
        quantity=quantity,
        fill_per_cylinder_kg=fill_per_cylinder,
        total_fill_kg=agent_required_kg,
        excess_kg=excess,
        warnings=warnings,
    )


def select_manifold_cylinders(
    room_id: str,
    agent_required_kg: float,
    agent_type: AgentType,
    catalog_df: pd.DataFrame,
    max_cylinders: int = 100,
) -> SelectedCylinder:
    return _select_equal_cylinders(room_id, agent_required_kg, agent_type, catalog_df, 2, max_cylinders)


def validate_forced_cylinder(
    room_id: str,
    agent_required_kg: float,
    agent_type: AgentType,
    catalog_df: pd.DataFrame,
    forced_cylinder_code: str,
    forced_cylinder_qty: int | None,
) -> SelectedCylinder:
    qty = forced_cylinder_qty or 1
    if qty <= 0:
        raise ValueError("La cantidad de cilindros forzada debe ser mayor que cero.")

    matches = catalog_df[catalog_df["cylinder_code"].astype(str) == str(forced_cylinder_code)]
    if matches.empty:
        raise ValueError("El cilindro forzado no existe en el catálogo.")

    row = matches.iloc[0]
    cylinder = _row_to_cylinder(row)
    if cylinder.agent_type != agent_type:
        raise ValueError("El cilindro forzado no corresponde al agente seleccionado.")

    fill_per_cylinder = agent_required_kg / qty
    if not (cylinder.min_fill_kg <= fill_per_cylinder <= cylinder.max_fill_kg):
        raise ValueError("El llenado por cilindro forzado está fuera del rango permitido.")

    return SelectedCylinder(
        room_id=room_id,
        cylinder=cylinder,
        quantity=qty,
        fill_per_cylinder_kg=fill_per_cylinder,
        total_fill_kg=agent_required_kg,
        excess_kg=(cylinder.max_fill_kg * qty) - agent_required_kg,
        is_forced=True,
    )


def _as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "si", "sí"}


def _recommended_max_fill_pct(row: pd.Series) -> float:
    value = row.get("recommended_max_fill_pct", 85)
    if pd.isna(value):
        return 85.0
    return float(value)


def _recommended_limit_with_tolerance(recommended_pct: float) -> float:
    return recommended_pct + 0.5


def _choose_best_candidate(
    candidates: list[tuple[bool, int, float, float, pd.Series]], min_quantity: int
) -> tuple[float, int, float, pd.Series]:
    if min_quantity <= 1:
        single_cylinder_candidates = [candidate for candidate in candidates if candidate[1] == 1]
        if single_cylinder_candidates:
            _, quantity, excess, fill_per_cylinder, row = sorted(
                single_cylinder_candidates, key=lambda item: (item[0], item[2])
            )[0]
            return excess, quantity, fill_per_cylinder, row

    _, quantity, excess, fill_per_cylinder, row = sorted(candidates, key=lambda item: (item[0], item[1], item[2]))[0]
    return excess, quantity, fill_per_cylinder, row


def _selection_warnings(quantity: int, min_quantity: int) -> list[str]:
    if quantity <= 1:
        return []
    if min_quantity >= 2:
        return ["Selección preliminar con cilindros iguales para configuración tipo manifold/main reserve."]
    return [
        "El agente requerido supera un cilindro simple; se seleccionaron múltiples cilindros iguales para esta sala."
    ]


def _with_added_warning(selected: SelectedCylinder, warning: str) -> SelectedCylinder:
    return SelectedCylinder(
        room_id=selected.room_id,
        cylinder=selected.cylinder,
        quantity=selected.quantity,
        fill_per_cylinder_kg=selected.fill_per_cylinder_kg,
        total_fill_kg=selected.total_fill_kg,
        excess_kg=selected.excess_kg,
        is_forced=selected.is_forced,
        warnings=[*selected.warnings, warning],
    )
