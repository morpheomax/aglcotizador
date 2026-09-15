import pytest

from src.bom.bom_builder import available_options, bom_lines_to_dataframe, build_optional_bom, build_system_bom
from src.bom.catalog_loader import (
    load_altitude_factors,
    load_bom_catalog,
    load_concentration_profiles,
    load_cylinder_catalog,
    load_dead_volume_factors,
    load_flooding_factors,
    load_optional_items,
)
from src.bom.consolidator import consolidate_bom
from src.engine.calculator import calculate_room_requirements, calculate_room_system
from src.engine.cylinder_selector import list_valid_cylinder_selections, select_cylinder
from src.models.room import AgentType, RoomInput
from src.models.system_config import SystemConfig, SystemType


def test_calculate_system_and_build_bom_with_options() -> None:
    room = RoomInput("R1", "Sala", AgentType.FM200, 10, 5, 3, design_concentration_pct=7.0)
    config = SystemConfig("R1", system_type=SystemType.SYSTEM, include_optional_items=True)

    result, selected_cylinder = calculate_room_system(
        room,
        config,
        load_flooding_factors(),
        load_altitude_factors(),
        load_cylinder_catalog(),
    )
    system_lines = build_system_bom(room, result, selected_cylinder, config, load_bom_catalog())
    options = available_options(room, config, load_optional_items())
    options.loc[:, "selected"] = True
    optional_lines = build_optional_bom(room, config, load_optional_items(), options, selected_cylinder)
    detail = bom_lines_to_dataframe(system_lines + optional_lines)
    consolidated = consolidate_bom(detail)

    assert result.agent_required_rounded_kg > 0
    assert selected_cylinder.quantity == 1
    assert "FM-200-SRL" in set(detail["code"])
    nozzle_rows = detail[
        detail["code"].astype(str).str.contains("NOZZLE", case=False)
        | detail["product"].astype(str).str.contains("NOZZLE", case=False)
    ]
    assert not nozzle_rows.empty
    assert set(nozzle_rows["quantity"]) == {2.0}
    assert len(optional_lines) > 0
    assert not consolidated.empty


def test_fk_room_matches_memory_software_concentrations_at_500_m() -> None:
    room = RoomInput(
        "R1",
        "Sala software",
        AgentType.FK5112,
        18,
        6,
        4,
        min_temp_c=16.0,
        max_temp_c=27.0,
        design_concentration_pct=4.52,
        altitude_m=500.0,
    )
    result = calculate_room_requirements(
        room,
        SystemConfig("R1"),
        load_flooding_factors(),
        load_altitude_factors(),
    )

    assert result.net_volume_m3 == pytest.approx(432.0)
    assert result.altitude_factor == pytest.approx(0.96)
    assert result.agent_required_exact_kg == pytest.approx(277.361325)
    assert result.agent_required_rounded_kg == 278.0
    assert result.minimum_concentration_achieved_pct == pytest.approx(4.5299366)
    assert result.maximum_concentration_achieved_pct == pytest.approx(4.7137303)


def test_concentration_profile_overrides_manual_concentration() -> None:
    room = RoomInput(
        "R1",
        "Sala perfil",
        AgentType.FK5112,
        18,
        6,
        4,
        min_temp_c=16.0,
        max_temp_c=27.0,
        design_concentration_pct=5.5,
        concentration_profile_id="FK_ULFM_C_452",
    )
    result = calculate_room_requirements(
        room,
        SystemConfig("R1"),
        load_flooding_factors(),
        load_altitude_factors(),
        concentration_profiles_df=load_concentration_profiles(),
    )

    assert result.design_concentration_applied_pct == 4.52
    assert result.concentration_profile_label == "UL/FM Class C (4.52%)"
    assert result.agent_required_exact_kg == pytest.approx(288.9180469)


def test_pipe_dead_volume_adds_stored_agent_but_not_room_concentration_mass() -> None:
    room = RoomInput(
        "R1",
        "Sala manifold",
        AgentType.FK5112,
        18,
        6,
        4,
        min_temp_c=16.0,
        max_temp_c=27.0,
        design_concentration_pct=4.52,
    )
    config = SystemConfig("R1", manifold_nominal_diameter_dn=65, reserve_sections_qty=1)
    result = calculate_room_requirements(
        room,
        config,
        load_flooding_factors(),
        load_altitude_factors(),
        dead_volume_factors_df=load_dead_volume_factors(),
    )

    assert result.pipe_dead_volume_l == pytest.approx(1.36)
    assert result.pipe_agent_allowance_kg == pytest.approx(2.176)
    assert result.enclosure_agent_required_exact_kg == pytest.approx(288.9180469)
    assert result.agent_required_exact_kg == pytest.approx(291.0940469)
    assert result.agent_required_rounded_kg == 292.0
    assert result.agent_available_to_enclosure_kg == pytest.approx(289.824)
    assert result.minimum_concentration_achieved_pct > 4.52


def test_manifold_selects_multiple_equal_cylinders() -> None:
    room = RoomInput("R1", "Sala", AgentType.FM200, 20, 10, 3, design_concentration_pct=7.0)
    config = SystemConfig("R1", system_type=SystemType.MANIFOLD)

    _, selected_cylinder = calculate_room_system(
        room,
        config,
        load_flooding_factors(),
        load_altitude_factors(),
        load_cylinder_catalog(),
    )

    assert selected_cylinder.quantity >= 2


def test_large_manifold_does_not_fail_with_many_equal_cylinders() -> None:
    room = RoomInput("R1", "Sala grande", AgentType.FM200, 60, 20, 4, design_concentration_pct=7.0)
    config = SystemConfig("R1", system_type=SystemType.MANIFOLD)

    result, selected_cylinder = calculate_room_system(
        room,
        config,
        load_flooding_factors(),
        load_altitude_factors(),
        load_cylinder_catalog(),
    )

    assert result.agent_required_rounded_kg > 0
    assert selected_cylinder.quantity >= 2


def test_very_large_system_does_not_block_agent_calculation() -> None:
    room = RoomInput("R1", "Sala muy grande", AgentType.FM200, 120, 40, 5, design_concentration_pct=7.0)
    config = SystemConfig("R1", system_type=SystemType.SYSTEM)

    result, selected_cylinder = calculate_room_system(
        room,
        config,
        load_flooding_factors(),
        load_altitude_factors(),
        load_cylinder_catalog(),
    )

    assert result.agent_required_rounded_kg > 0
    assert selected_cylinder.quantity > 1
    assert selected_cylinder.fill_per_cylinder_kg <= selected_cylinder.cylinder.max_fill_kg


def test_system_falls_back_to_multiple_equal_cylinders_when_single_is_not_enough() -> None:
    room = RoomInput("R1", "Sala grande", AgentType.FM200, 20, 10, 3, design_concentration_pct=7.0)
    config = SystemConfig("R1", system_type=SystemType.SYSTEM)

    result, selected_cylinder = calculate_room_system(
        room,
        config,
        load_flooding_factors(),
        load_altitude_factors(),
        load_cylinder_catalog(),
    )
    system_lines = build_system_bom(room, result, selected_cylinder, config, load_bom_catalog())
    detail = bom_lines_to_dataframe(system_lines)

    assert selected_cylinder.quantity >= 1
    assert selected_cylinder.cylinder.max_fill_kg >= selected_cylinder.fill_per_cylinder_kg
    cylinder_rows = detail[detail["code"] == selected_cylinder.cylinder.cylinder_code]
    assert cylinder_rows["quantity"].iloc[0] == selected_cylinder.quantity


def test_multiple_rooms_generate_consolidated_bom() -> None:
    rooms_and_configs = [
        (
            RoomInput("R1", "Sala 1", AgentType.FM200, 10, 5, 3, design_concentration_pct=7.0),
            SystemConfig("R1", system_type=SystemType.SYSTEM),
        ),
        (
            RoomInput("R2", "Sala 2", AgentType.FK5112, 12, 6, 3, design_concentration_pct=4.5),
            SystemConfig("R2", system_type=SystemType.SYSTEM),
        ),
    ]
    all_lines = []

    for room, config in rooms_and_configs:
        result, selected_cylinder = calculate_room_system(
            room,
            config,
            load_flooding_factors(),
            load_altitude_factors(),
            load_cylinder_catalog(),
        )
        all_lines.extend(build_system_bom(room, result, selected_cylinder, config, load_bom_catalog()))

    detail = bom_lines_to_dataframe(all_lines)
    consolidated = consolidate_bom(detail)

    assert detail["room_id"].nunique() == 2
    assert "FM-200-SRL" in set(consolidated["code"])
    assert "FK-5-1-12" in set(consolidated["code"])


def test_independent_rooms_with_different_agents_calculate_independently() -> None:
    rooms_and_configs = [
        (RoomInput("R1", "Sala FM", AgentType.FM200, 20, 10, 3, design_concentration_pct=7.0), SystemConfig("R1")),
        (RoomInput("R2", "Sala FK", AgentType.FK5112, 18, 8, 3, design_concentration_pct=4.5), SystemConfig("R2")),
    ]

    results = []
    cylinders = []
    for room, config in rooms_and_configs:
        result, selected_cylinder = calculate_room_system(
            room,
            config,
            load_flooding_factors(),
            load_altitude_factors(),
            load_cylinder_catalog(),
        )
        results.append(result)
        cylinders.append(selected_cylinder)

    assert {result.room_id for result in results} == {"R1", "R2"}
    assert cylinders[0].cylinder.agent_type == AgentType.FM200
    assert cylinders[1].cylinder.agent_type == AgentType.FK5112


def test_small_fk_room_selects_small_cylinder_from_excel_catalog() -> None:
    room = RoomInput("R1", "Sala pequeña FK", AgentType.FK5112, 2, 4, 2.5, design_concentration_pct=4.5, altitude_m=1)
    config = SystemConfig("R1", system_type=SystemType.SYSTEM)

    result, selected_cylinder = calculate_room_system(
        room,
        config,
        load_flooding_factors(),
        load_altitude_factors(),
        load_cylinder_catalog(),
    )

    assert result.agent_required_rounded_kg > 0
    assert result.agent_required_rounded_kg * 2.2046226218 > 0
    assert selected_cylinder.cylinder.cylinder_label in {"TANK SIZE 16L", "TANK SIZE 32L"}
    assert selected_cylinder.fill_per_cylinder_kg <= selected_cylinder.cylinder.max_fill_kg
    fill_pct = (selected_cylinder.fill_per_cylinder_kg / selected_cylinder.cylinder.max_fill_kg) * 100
    assert 65 <= fill_pct <= 75
    assert selected_cylinder.cylinder.recommended_max_fill_pct == 85


def test_small_fm200_room_selects_one_16l_cylinder() -> None:
    room = RoomInput("R1", "Sala pequeña FM", AgentType.FM200, 2, 4, 2.5, design_concentration_pct=7.0, altitude_m=1)
    config = SystemConfig("R1", system_type=SystemType.SYSTEM)

    result, selected_cylinder = calculate_room_system(
        room,
        config,
        load_flooding_factors(),
        load_altitude_factors(),
        load_cylinder_catalog(),
    )

    assert result.agent_required_rounded_kg > 0
    assert selected_cylinder.quantity == 1
    assert selected_cylinder.cylinder.cylinder_label == "TANK SIZE 16L"
    assert selected_cylinder.fill_per_cylinder_kg <= selected_cylinder.cylinder.max_fill_kg
    assert (selected_cylinder.fill_per_cylinder_kg / selected_cylinder.cylinder.max_fill_kg) * 100 <= 85


def test_fm200_official_factor_prefers_single_16l_instead_of_multiple_8l() -> None:
    room = RoomInput("R1", "Sala FM", AgentType.FM200, 2, 4, 2.5, design_concentration_pct=8.1, altitude_m=1)
    config = SystemConfig("R1", system_type=SystemType.SYSTEM)

    result, selected_cylinder = calculate_room_system(
        room,
        config,
        load_flooding_factors(),
        load_altitude_factors(),
        load_cylinder_catalog(),
    )

    assert round(result.agent_required_rounded_kg * 2.2046226218, 1) == 28.7
    assert selected_cylinder.quantity == 1
    assert selected_cylinder.cylinder.cylinder_label == "TANK SIZE 16L"
    assert not any("margen recomendado" in warning for warning in result.warnings)


def test_forced_fm200_16l_cylinder_is_respected() -> None:
    room = RoomInput("R1", "Sala FM", AgentType.FM200, 2, 4, 2.5, design_concentration_pct=8.1, altitude_m=1)
    config = SystemConfig(
        "R1",
        system_type=SystemType.SYSTEM,
        force_cylinder=True,
        forced_cylinder_code="445733",
        forced_cylinder_qty=1,
    )

    _, selected_cylinder = calculate_room_system(
        room,
        config,
        load_flooding_factors(),
        load_altitude_factors(),
        load_cylinder_catalog(),
    )

    assert selected_cylinder.cylinder.cylinder_label == "TANK SIZE 16L"
    assert selected_cylinder.quantity == 1


def test_automatic_selection_rejects_fill_below_every_cylinder_minimum() -> None:
    with pytest.raises(ValueError, match="rango mínimo/máximo"):
        select_cylinder(
            room_id="R1",
            agent_required_kg=1.0,
            agent_type=AgentType.FM200,
            system_type=SystemType.SYSTEM,
            catalog_df=load_cylinder_catalog(),
        )


@pytest.mark.parametrize("agent_required_kg", [4.0, 8.0])
def test_forced_fm200_8l_accepts_exact_manual_fill_limits(agent_required_kg: float) -> None:
    selected = select_cylinder(
        room_id="R1",
        agent_required_kg=agent_required_kg,
        agent_type=AgentType.FM200,
        system_type=SystemType.SYSTEM,
        catalog_df=load_cylinder_catalog(),
        forced_cylinder_code="445732",
        forced_cylinder_qty=1,
    )

    assert selected.fill_per_cylinder_kg == agent_required_kg


def test_cylinder_alternatives_include_valid_single_and_multiple_configurations() -> None:
    alternatives = list_valid_cylinder_selections(
        room_id="R1",
        agent_required_kg=30.0,
        agent_type=AgentType.FM200,
        system_type=SystemType.SYSTEM,
        catalog_df=load_cylinder_catalog(),
    )

    configurations = {(item.cylinder.cylinder_label, item.quantity) for item in alternatives}
    assert ("TANK SIZE 32L", 1) in configurations
    assert ("TANK SIZE 16L", 2) in configurations
    assert all(
        item.cylinder.min_fill_kg <= item.fill_per_cylinder_kg <= item.cylinder.max_fill_kg
        for item in alternatives
    )
