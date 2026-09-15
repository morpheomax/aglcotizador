from src.bom.catalog_loader import load_flooding_factors


def test_fm200_flooding_factors_do_not_include_decimal_outliers() -> None:
    df = load_flooding_factors()
    fm200 = df[df["agent_type"] == "FM-200"]

    assert fm200["flooding_factor_imperial"].max() < 0.2
    assert fm200["flooding_factor_metric"].max() < 2.0


def test_fm200_corrected_8_percent_low_temperature_factor() -> None:
    df = load_flooding_factors()
    row = df[
        (df["agent_type"] == "FM-200")
        & (df["concentration_pct"] == 8.0)
        & (df["temperature_f"] == 10)
    ].iloc[0]

    assert row["flooding_factor_imperial"] == 0.045
