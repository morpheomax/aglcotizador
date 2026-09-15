from datetime import date

from src.models import (
    AgentType,
    BomLine,
    CylinderOption,
    ProjectInfo,
    RoomCalculationResult,
    RoomInput,
    SelectedCylinder,
    SystemConfig,
    SystemType,
)


def test_core_models_can_be_instantiated() -> None:
    project = ProjectInfo("Cliente", "Proyecto", "Chile", "Santiago", 0, "USD", None, date.today())
    room = RoomInput("R1", "Sala", AgentType.FM200, 10, 5, 3)
    config = SystemConfig("R1", system_type=SystemType.SYSTEM)
    result = RoomCalculationResult("R1", 50, 150, 0, 0, 150, 150, 0.65, 1.0, 97.5, 97.5, 2)
    cylinder = CylinderOption(AgentType.FM200, "TANK SIZE 106L", "FM200-106L", 106, 40, 130, 50)
    selected = SelectedCylinder("R1", cylinder, 1, 97.5, 97.5, 32.5)
    line = BomLine(None, "R1", "Sala", "SISTEMA", "SISTEMA", AgentType.FM200, "TANK SIZE 106L", None, "X", "Item", "un", 1, None, None, None)

    assert project.client == "Cliente"
    assert room.agent_type == AgentType.FM200
    assert config.system_type == SystemType.SYSTEM
    assert result.net_volume_m3 == 150
    assert selected.cylinder.cylinder_code == "FM200-106L"
    assert line.quantity == 1
