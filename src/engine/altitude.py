"""Altitude correction calculations."""

from __future__ import annotations

import pandas as pd


_OPTIONAL_CORRECTION_LIMIT_M = 914.0


def get_altitude_factor(
    altitude_m: float,
    altitude_factors_df: pd.DataFrame,
    interpolate: bool = False,
) -> tuple[float, list[str]]:
    if altitude_factors_df.empty:
        raise ValueError("No hay catálogo de altitud cargado.")

    required_columns = {"altitude_m", "altitude_ft", "correction_factor"}
    if not required_columns.issubset(altitude_factors_df.columns):
        raise ValueError("El catálogo de altitud no contiene las columnas requeridas.")

    if altitude_m < 0 and altitude_m >= -_OPTIONAL_CORRECTION_LIMIT_M:
        return 1.0, []

    df = altitude_factors_df.copy()
    df["altitude_m"] = df["altitude_m"].astype(float)
    df["altitude_ft"] = df["altitude_ft"].astype(float)
    df["correction_factor"] = df["correction_factor"].astype(float)
    df = df.sort_values("altitude_ft")
    minimum = float(df["altitude_m"].min())
    maximum = float(df["altitude_m"].max())
    if altitude_m < minimum or altitude_m > maximum:
        raise ValueError(
            f"La altitud está fuera del rango publicado por NFPA 2001: "
            f"{minimum:g} m a {maximum:g} m."
        )

    altitude_ft = altitude_m * 3.280839895
    if not interpolate:
        lower_rows = df[df["altitude_ft"] <= altitude_ft]
        if lower_rows.empty:
            return 1.0, []
        return float(lower_rows.iloc[-1]["correction_factor"]), []

    df = df.sort_values("altitude_m")
    lower = df[df["altitude_m"] <= altitude_m].iloc[-1]
    upper = df[df["altitude_m"] >= altitude_m].iloc[0]
    lower_altitude = float(lower["altitude_m"])
    upper_altitude = float(upper["altitude_m"])
    if lower_altitude == upper_altitude:
        return float(lower["correction_factor"]), []

    fraction = (altitude_m - lower_altitude) / (upper_altitude - lower_altitude)
    factor = float(lower["correction_factor"]) + fraction * (
        float(upper["correction_factor"]) - float(lower["correction_factor"])
    )
    return factor, []
