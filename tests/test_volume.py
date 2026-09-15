import pytest

from src.engine.volume import calculate_area, calculate_net_volume
from src.models.room import AgentType, RoomInput


def test_simple_volume() -> None:
    room = RoomInput("R1", "Sala", AgentType.FM200, 10, 5, 3)

    assert calculate_area(room.length_m, room.width_m) == 50
    assert calculate_net_volume(room) == 150


def test_reductions_cannot_exceed_gross_volume() -> None:
    room = RoomInput("R1", "Sala", AgentType.FM200, 10, 5, 2, structural_reductions_m3=120)

    with pytest.raises(ValueError, match="reducciones"):
        calculate_net_volume(room)


def test_unprotected_floor_and_ceiling_are_excluded_from_agent_volume() -> None:
    room = RoomInput(
        "R1",
        "Sala",
        AgentType.FM200,
        10,
        5,
        3,
        raised_floor_m=0.5,
        false_ceiling_m=0.5,
        protect_raised_floor=False,
        protect_false_ceiling=False,
    )

    assert calculate_net_volume(room) == 150


def test_protected_floor_requires_a_positive_height() -> None:
    room = RoomInput("R1", "Sala", AgentType.FM200, 10, 5, 3, protect_raised_floor=True)

    with pytest.raises(ValueError, match="piso técnico"):
        calculate_net_volume(room)


def test_object_reductions_must_be_permanent_non_permeable_objects() -> None:
    room = RoomInput(
        "R1",
        "Sala",
        AgentType.FM200,
        10,
        5,
        3,
        object_reductions_m3=10,
        object_reductions_are_permanent=False,
    )

    with pytest.raises(ValueError, match="objetos sólidos"):
        calculate_net_volume(room)
