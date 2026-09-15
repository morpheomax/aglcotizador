import pytest

from src.engine.nozzles import calculate_room_nozzles
from src.models.room import AgentType, RoomInput
from src.models.system_config import SystemConfig


def _room(**changes: object) -> RoomInput:
    values: dict[str, object] = {
        "room_id": "R1",
        "name": "Sala",
        "agent_type": AgentType.FM200,
        "length_m": 5.0,
        "width_m": 5.0,
        "height_m": 3.0,
    }
    values.update(changes)
    return RoomInput(**values)


def test_small_room_recommends_two_nozzles_by_internal_even_policy() -> None:
    result = calculate_room_nozzles(_room(), SystemConfig("R1"), 95.3)

    assert result.manufacturer_min_qty == 1
    assert result.recommended_qty == 2
    assert result.final_qty == 2


def test_room_floor_and_ceiling_allow_three_single_nozzles() -> None:
    room = _room(
        raised_floor_m=0.5,
        false_ceiling_m=0.4,
        protect_raised_floor=True,
        protect_false_ceiling=True,
    )

    result = calculate_room_nozzles(room, SystemConfig("R1"), 95.3)

    assert result.manufacturer_min_qty == 3
    assert result.recommended_qty == 3
    assert len(result.areas) == 3


def test_unprotected_subspaces_do_not_add_nozzles() -> None:
    room = _room(
        raised_floor_m=0.5,
        false_ceiling_m=0.4,
        protect_raised_floor=False,
        protect_false_ceiling=False,
    )

    result = calculate_room_nozzles(room, SystemConfig("R1"), 95.3)

    assert result.manufacturer_min_qty == 1


def test_odd_manual_nozzle_quantity_requires_reason() -> None:
    config = SystemConfig("R1", override_nozzles=True, nozzle_qty_manual=3)

    with pytest.raises(ValueError, match="justificación"):
        calculate_room_nozzles(_room(), config, 95.3)


def test_manual_nozzle_quantity_cannot_be_below_manufacturer_minimum() -> None:
    room = _room(length_m=20.0, width_m=10.0)
    config = SystemConfig("R1", override_nozzles=True, nozzle_qty_manual=2)

    with pytest.raises(ValueError, match="menor al mínimo técnico"):
        calculate_room_nozzles(room, config, 95.3)


def test_more_than_twenty_nozzles_requires_engineering_review() -> None:
    result = calculate_room_nozzles(_room(length_m=50.0, width_m=50.0), SystemConfig("R1"), 95.3)

    assert result.final_qty > 20
    assert any("supera el máximo" in warning for warning in result.warnings)
