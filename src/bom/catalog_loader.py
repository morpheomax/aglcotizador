"""Catalog loading utilities for BOM and technical data."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


PROCESSED_DATA_DIR = Path("data/processed")


def load_processed_catalog(file_name: str) -> pd.DataFrame:
    path = PROCESSED_DATA_DIR / file_name
    if not path.exists():
        raise FileNotFoundError(f"No se encontró el catálogo procesado: {path}")
    return pd.read_csv(path)


def load_bom_catalog() -> pd.DataFrame:
    return load_processed_catalog("bom_catalog.csv")


def load_optional_items() -> pd.DataFrame:
    return load_processed_catalog("optional_items.csv")


def load_cylinder_catalog() -> pd.DataFrame:
    return load_processed_catalog("cylinder_catalog.csv")


def load_flooding_factors() -> pd.DataFrame:
    return load_processed_catalog("flooding_factors.csv")


def load_altitude_factors() -> pd.DataFrame:
    return load_processed_catalog("altitude_factors.csv")


def load_nozzle_coverage() -> pd.DataFrame:
    return load_processed_catalog("nozzle_coverage.csv")


def load_concentration_profiles() -> pd.DataFrame:
    return load_processed_catalog("concentration_profiles.csv")


def load_dead_volume_factors() -> pd.DataFrame:
    return load_processed_catalog("dead_volume_factors.csv")
