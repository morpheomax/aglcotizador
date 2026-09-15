"""Shared technical validations for calculation inputs."""

from __future__ import annotations


def validate_positive(value: float, field_name: str) -> None:
    if value <= 0:
        raise ValueError(f"{field_name} debe ser mayor que cero.")


def validate_non_negative(value: float, field_name: str) -> None:
    if value < 0:
        raise ValueError(f"{field_name} no puede ser negativo.")
