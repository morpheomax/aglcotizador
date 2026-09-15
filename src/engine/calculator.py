"""High-level calculation orchestration for one room."""

from __future__ import annotations

import pandas as pd

from src.engine.agent import (
    calculate_achieved_concentration,
    calculate_required_agent,
    get_flooding_factor,
    round_agent_quantity,
)
from src.engine.altitude import get_altitude_factor
from src.engine.concentration_profiles import resolve_design_concentration
from src.engine.cylinder_selector import select_cylinder
from src.engine.dead_volume import calculate_dead_volume_l, calculate_pipe_agent_allowance
from src.engine.nozzles import calculate_room_nozzles, get_nozzle_coverage
from src.engine.volume import (
    calculate_area,
    calculate_false_ceiling_volume,
    calculate_gross_volume,
    calculate_net_volume,
    calculate_raised_floor_volume,
    calculate_room_volume,
)
from src.models.cylinder import SelectedCylinder
from src.models.room import RoomCalculationResult, RoomInput
from src.models.system_config import SystemConfig


def calculate_room_system(
    room: RoomInput,
    config: SystemConfig,
    flooding_factors_df: pd.DataFrame,
    altitude_factors_df: pd.DataFrame,
    cylinder_catalog_df: pd.DataFrame,
    nozzle_coverage_m2: float | None = None,
    nozzle_catalog_df: pd.DataFrame | None = None,
    concentration_profiles_df: pd.DataFrame | None = None,
    dead_volume_factors_df: pd.DataFrame | None = None,
) -> tuple[RoomCalculationResult, SelectedCylinder]:
    result = calculate_room_requirements(
        room,
        config,
        flooding_factors_df,
        altitude_factors_df,
        nozzle_coverage_m2,
        nozzle_catalog_df,
        concentration_profiles_df,
        dead_volume_factors_df,
    )
    selected_cylinder = select_cylinder(
        room_id=room.room_id,
        agent_required_kg=result.agent_required_rounded_kg,
        agent_type=room.agent_type,
        system_type=config.system_type,
        catalog_df=cylinder_catalog_df,
        forced_cylinder_code=config.forced_cylinder_code if config.force_cylinder else None,
        forced_cylinder_qty=config.forced_cylinder_qty if config.force_cylinder else None,
    )
    result.warnings.extend(selected_cylinder.warnings)
    return result, selected_cylinder


def calculate_room_requirements(
    room: RoomInput,
    config: SystemConfig,
    flooding_factors_df: pd.DataFrame,
    altitude_factors_df: pd.DataFrame,
    nozzle_coverage_m2: float | None = None,
    nozzle_catalog_df: pd.DataFrame | None = None,
    concentration_profiles_df: pd.DataFrame | None = None,
    dead_volume_factors_df: pd.DataFrame | None = None,
) -> RoomCalculationResult:
    warnings: list[str] = []
    area_m2 = calculate_area(room.length_m, room.width_m)
    volume_room_m3 = calculate_room_volume(room.length_m, room.width_m, room.height_m)
    volume_raised_floor_m3 = (
        calculate_raised_floor_volume(room.length_m, room.width_m, room.raised_floor_m)
        if room.protect_raised_floor
        else 0.0
    )
    volume_false_ceiling_m3 = (
        calculate_false_ceiling_volume(room.length_m, room.width_m, room.false_ceiling_m)
        if room.protect_false_ceiling
        else 0.0
    )
    gross_volume_m3 = calculate_gross_volume(room)
    net_volume_m3 = calculate_net_volume(room)

    design_concentration_pct, profile_label, occupied_max_pct, profile_warnings = resolve_design_concentration(
        room.agent_type,
        room.design_concentration_pct,
        room.concentration_profile_id,
        concentration_profiles_df,
    )
    warnings.extend(profile_warnings)
    flooding_factor = get_flooding_factor(
        room.agent_type,
        design_concentration_pct,
        room.min_temp_c,
        flooding_factors_df,
    )
    altitude_factor, altitude_warnings = get_altitude_factor(room.altitude_m, altitude_factors_df)
    warnings.extend(altitude_warnings)
    enclosure_agent_exact_kg = calculate_required_agent(net_volume_m3, flooding_factor, altitude_factor)
    pipe_dead_volume_l = calculate_dead_volume_l(
        config.manifold_nominal_diameter_dn,
        config.reserve_sections_qty,
        config.custom_dead_volume_l,
        dead_volume_factors_df,
    )
    pipe_agent_allowance_kg = calculate_pipe_agent_allowance(room.agent_type, pipe_dead_volume_l)
    agent_exact_kg = enclosure_agent_exact_kg + pipe_agent_allowance_kg
    agent_rounded_kg = round_agent_quantity(agent_exact_kg)
    agent_available_to_enclosure_kg = agent_rounded_kg - pipe_agent_allowance_kg
    minimum_concentration_achieved_pct = calculate_achieved_concentration(
        agent_available_to_enclosure_kg,
        net_volume_m3,
        room.agent_type,
        room.min_temp_c,
        altitude_factor,
    )
    maximum_concentration_achieved_pct = calculate_achieved_concentration(
        agent_available_to_enclosure_kg,
        net_volume_m3,
        room.agent_type,
        room.max_temp_c,
        altitude_factor,
    )
    if minimum_concentration_achieved_pct + 1e-9 < design_concentration_pct:
        warnings.append("La concentración mínima lograda queda bajo el perfil de diseño seleccionado.")
    if occupied_max_pct is not None and maximum_concentration_achieved_pct > occupied_max_pct:
        warnings.append(
            f"La concentración máxima lograda supera {occupied_max_pct:g}% para espacio ocupado; "
            "requiere revisión de exposición, evacuación y autoridad competente."
        )
    if nozzle_coverage_m2 is None:
        if nozzle_catalog_df is None:
            nozzle_coverage_m2 = 95.3 if room.agent_type.value == "FM-200" else 96.0
            max_nozzles = 20
        else:
            nozzle_coverage_m2, max_nozzles = get_nozzle_coverage(room.agent_type, nozzle_catalog_df)
    else:
        max_nozzles = 20
    nozzle_result = calculate_room_nozzles(room, config, nozzle_coverage_m2, max_nozzles)
    warnings.extend(nozzle_result.warnings)
    area_summary = ", ".join(f"{area.area_type.value}: {area.minimum_qty}" for area in nozzle_result.areas)

    return RoomCalculationResult(
        room_id=room.room_id,
        area_m2=area_m2,
        volume_room_m3=volume_room_m3,
        volume_raised_floor_m3=volume_raised_floor_m3,
        volume_false_ceiling_m3=volume_false_ceiling_m3,
        gross_volume_m3=gross_volume_m3,
        net_volume_m3=net_volume_m3,
        flooding_factor=flooding_factor,
        altitude_factor=altitude_factor,
        agent_required_exact_kg=agent_exact_kg,
        agent_required_rounded_kg=agent_rounded_kg,
        minimum_concentration_achieved_pct=minimum_concentration_achieved_pct,
        maximum_concentration_achieved_pct=maximum_concentration_achieved_pct,
        nozzle_min_qty=nozzle_result.manufacturer_min_qty,
        nozzle_recommended_qty=nozzle_result.recommended_qty,
        nozzle_final_qty=nozzle_result.final_qty,
        nozzle_area_summary=area_summary,
        hydraulic_validation_required=nozzle_result.hydraulic_validation_required,
        warnings=warnings,
        concentration_profile_label=profile_label,
        design_concentration_applied_pct=design_concentration_pct,
        occupied_max_concentration_pct=occupied_max_pct,
        enclosure_agent_required_exact_kg=enclosure_agent_exact_kg,
        pipe_dead_volume_l=pipe_dead_volume_l,
        pipe_agent_allowance_kg=pipe_agent_allowance_kg,
        agent_available_to_enclosure_kg=agent_available_to_enclosure_kg,
    )
