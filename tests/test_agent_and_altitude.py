import pandas as pd
import pytest

from src.bom.catalog_loader import load_altitude_factors, load_flooding_factors
from src.engine.agent import calculate_required_agent, get_flooding_factor
from src.engine.altitude import get_altitude_factor
from src.models.room import AgentType


@pytest.mark.parametrize(
    ("agent_type", "temperature_c", "concentration_pct", "expected_factor"),
    [
        (AgentType.FM200, 20.0, 7.2, 0.565653803),
        (AgentType.FK5112, 21.0, 4.5, 0.653053453),
    ],
)
def test_flooding_factor_uses_official_equation(
    agent_type: AgentType,
    temperature_c: float,
    concentration_pct: float,
    expected_factor: float,
) -> None:
    factor = get_flooding_factor(
        agent_type,
        concentration_pct,
        temperature_c,
        load_flooding_factors(),
    )

    assert factor == pytest.approx(expected_factor, rel=1e-6)


@pytest.mark.parametrize(
    ("agent_type", "temperature_c", "concentration_pct"),
    [
        (AgentType.FM200, -10.1, 7.0),
        (AgentType.FM200, 55.1, 7.0),
        (AgentType.FM200, 20.0, 6.3),
        (AgentType.FM200, 20.0, 15.1),
        (AgentType.FK5112, -20.1, 4.5),
        (AgentType.FK5112, 65.1, 4.5),
        (AgentType.FK5112, 20.0, 3.9),
        (AgentType.FK5112, 20.0, 10.1),
    ],
)
def test_flooding_factor_rejects_values_outside_manual_table_domain(
    agent_type: AgentType,
    temperature_c: float,
    concentration_pct: float,
) -> None:
    with pytest.raises(ValueError, match="fuera del rango publicado"):
        get_flooding_factor(
            agent_type,
            concentration_pct,
            temperature_c,
            load_flooding_factors(),
        )


@pytest.mark.parametrize("altitude_m", [-914.0, 0.0, 50.0])
def test_altitude_factor_is_one_below_first_positive_step(altitude_m: float) -> None:
    factor, warnings = get_altitude_factor(altitude_m, load_altitude_factors())

    assert factor == 1.0
    assert warnings == []


@pytest.mark.parametrize(
    ("altitude_m", "expected_factor"),
    [
        (500.0, 0.96),
        (914.0, 0.93),
        (1000.0, 0.89),
    ],
)
def test_altitude_factor_uses_lower_nfpa_table_step_by_default(
    altitude_m: float,
    expected_factor: float,
) -> None:
    factor, warnings = get_altitude_factor(altitude_m, load_altitude_factors())

    assert factor == pytest.approx(expected_factor)
    assert warnings == []


def test_altitude_factor_can_interpolate_when_requested() -> None:
    factor, warnings = get_altitude_factor(
        500.0,
        load_altitude_factors(),
        interpolate=True,
    )

    assert factor == pytest.approx(0.940787402)
    assert warnings == []


def test_altitude_factor_interpolates_nfpa_table_above_optional_band() -> None:
    factor, warnings = get_altitude_factor(1066.8, load_altitude_factors(), interpolate=True)

    assert factor == pytest.approx(0.875)
    assert warnings == []


@pytest.mark.parametrize("altitude_m", [-915.0, 3049.0])
def test_altitude_factor_rejects_values_without_published_nfpa_factor(altitude_m: float) -> None:
    with pytest.raises(ValueError, match="fuera del rango publicado"):
        get_altitude_factor(altitude_m, load_altitude_factors())


def test_altitude_factor_requires_catalog() -> None:
    with pytest.raises(ValueError, match="No hay catálogo de altitud"):
        get_altitude_factor(1000.0, pd.DataFrame())


def test_reported_fk_room_matches_memory_software_at_50_m_optional_band() -> None:
    flooding_factor = get_flooding_factor(
        AgentType.FK5112,
        4.52,
        16.0,
        load_flooding_factors(),
    )
    altitude_factor, warnings = get_altitude_factor(50.0, load_altitude_factors())
    agent_kg = calculate_required_agent(432.0, flooding_factor, altitude_factor)

    assert warnings == []
    assert flooding_factor == pytest.approx(0.668791775)
    assert altitude_factor == 1.0
    assert agent_kg == pytest.approx(288.9180469)
    assert round(agent_kg, 2) == 288.92


def test_reported_fk_room_matches_memory_software_at_500_m_minimum_concentration() -> None:
    flooding_factor = get_flooding_factor(
        AgentType.FK5112,
        4.52,
        16.0,
        load_flooding_factors(),
    )
    altitude_factor, warnings = get_altitude_factor(500.0, load_altitude_factors())
    agent_kg = calculate_required_agent(432.0, flooding_factor, altitude_factor)

    assert warnings == []
    assert altitude_factor == 0.96
    assert agent_kg == pytest.approx(277.361325)
    assert round(agent_kg, 2) == 277.36


def test_reported_fk_room_matches_memory_software_at_500_m_adjusted_concentration() -> None:
    flooding_factor = get_flooding_factor(
        AgentType.FK5112,
        4.53,
        16.0,
        load_flooding_factors(),
    )
    altitude_factor, warnings = get_altitude_factor(500.0, load_altitude_factors())
    agent_kg = calculate_required_agent(432.0, flooding_factor, altitude_factor)

    assert warnings == []
    assert altitude_factor == 0.96
    assert agent_kg == pytest.approx(278.0040727)
    assert round(agent_kg, 2) == 278.00
