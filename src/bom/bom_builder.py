"""Base BOM generation rules."""

from __future__ import annotations

import pandas as pd

from src.models.bom import BomLine
from src.models.cylinder import SelectedCylinder
from src.models.room import RoomCalculationResult, RoomInput
from src.models.system_config import SystemConfig, SystemType


AGENT_CODES = {"FM-200": {"FM200-AGENT", "FM-200-SRL"}, "FK-5-1-12": {"FK5112-AGENT", "FK-5-1-12"}}
SERVICE_CHARGE_CODE = "AGLIMP-RECARGA-00"


def build_system_bom(
    room: RoomInput,
    result: RoomCalculationResult,
    selected_cylinder: SelectedCylinder,
    config: SystemConfig,
    catalog_df: pd.DataFrame,
    project_id: str | None = None,
) -> list[BomLine]:
    if catalog_df.empty:
        raise ValueError("No hay catálogo BOM cargado.")

    df = catalog_df[catalog_df["enabled"].map(_as_bool)].copy()
    system_rows = df[
        (df["bom_type"] == SystemType.SYSTEM.value)
        & (df["agent_type"] == room.agent_type.value)
        & (df["cylinder_label"] == selected_cylinder.cylinder.cylinder_label)
    ]
    manifold_rows = pd.DataFrame()
    if config.system_type == SystemType.MANIFOLD:
        manifold_rows = df[
            (df["bom_type"] == SystemType.MANIFOLD.value)
            & (df["agent_type"] == room.agent_type.value)
        ]

    lines: list[BomLine] = []
    for _, row in pd.concat([system_rows, manifold_rows]).sort_values("item_order").iterrows():
        lines.append(_row_to_bom_line(row, room, result, selected_cylinder, config, project_id))
    return lines


def build_optional_bom(
    room: RoomInput,
    config: SystemConfig,
    optional_items_df: pd.DataFrame,
    selected_options_df: pd.DataFrame,
    selected_cylinder: SelectedCylinder,
    project_id: str | None = None,
) -> list[BomLine]:
    if not config.include_optional_items or selected_options_df.empty:
        return []

    lines: list[BomLine] = []
    for _, row in selected_options_df.iterrows():
        if not bool(row.get("selected", False)):
            continue
        unit_price = _nullable_float(row.get("unit_price"))
        quantity = float(row.get("quantity", row.get("default_qty", 1)) or 0)
        total_price = None if unit_price is None else unit_price * quantity
        lines.append(
            BomLine(
                project_id=project_id,
                room_id=room.room_id,
                room_name=room.name,
                system_type=config.system_type.value,
                bom_type="OPCIONAL",
                agent_type=room.agent_type,
                cylinder_label=selected_cylinder.cylinder.cylinder_label,
                brand=None,
                code=str(row["code"]),
                product=str(row["product"]),
                unit=str(row["unit"]),
                quantity=quantity,
                unit_price=unit_price,
                total_price=total_price,
                delivery=None,
                selected=True,
                notes=None if pd.isna(row.get("notes")) else str(row.get("notes")),
            )
        )
    return lines


def available_options(room: RoomInput, config: SystemConfig, optional_items_df: pd.DataFrame) -> pd.DataFrame:
    if optional_items_df.empty:
        return optional_items_df
    df = optional_items_df[
        (optional_items_df["agent_type"] == room.agent_type.value)
        & (optional_items_df["system_type"].isin([config.system_type.value, SystemType.SYSTEM.value]))
    ].copy()
    df["selected"] = df["selected_by_default"].map(_as_bool)
    df["quantity"] = df["default_qty"].astype(float)
    return df


def bom_lines_to_dataframe(lines: list[BomLine]) -> pd.DataFrame:
    return pd.DataFrame([line.__dict__ for line in lines])


def _row_to_bom_line(
    row: pd.Series,
    room: RoomInput,
    result: RoomCalculationResult,
    selected_cylinder: SelectedCylinder,
    config: SystemConfig,
    project_id: str | None,
) -> BomLine:
    quantity = float(row["quantity_base"])
    code = str(row["code"])
    product = str(row["product"])
    if code in AGENT_CODES.get(room.agent_type.value, set()):
        quantity = result.agent_required_rounded_kg
    elif code == selected_cylinder.cylinder.cylinder_code:
        quantity = float(selected_cylinder.quantity)
    elif "NOZZLE" in code.upper() or "NOZZLE" in product.upper():
        quantity = float(result.nozzle_final_qty or result.nozzle_min_qty)
    elif code == SERVICE_CHARGE_CODE:
        quantity = float(selected_cylinder.quantity)
    elif config.system_type == SystemType.MANIFOLD and row["bom_type"] == SystemType.SYSTEM.value:
        quantity = quantity * selected_cylinder.quantity
    elif selected_cylinder.quantity > 1 and code.startswith("DISCHARGE"):
        quantity = quantity * selected_cylinder.quantity

    unit_price = _nullable_float(row.get("unit_price"))
    total_price = None if unit_price is None else unit_price * quantity
    return BomLine(
        project_id=project_id,
        room_id=room.room_id,
        room_name=room.name,
        system_type=config.system_type.value,
        bom_type=str(row["bom_type"]),
        agent_type=room.agent_type,
        cylinder_label=selected_cylinder.cylinder.cylinder_label,
        brand=None if pd.isna(row.get("brand")) else str(row.get("brand")),
        code=code,
        product=product,
        unit=str(row["unit"]),
        quantity=quantity,
        unit_price=unit_price,
        total_price=total_price,
        delivery=None if pd.isna(row.get("delivery")) else str(row.get("delivery")),
        selected=True,
    )


def _nullable_float(value: object) -> float | None:
    if value is None or pd.isna(value) or value == "":
        return None
    return float(value)


def _as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "si", "sí"}
