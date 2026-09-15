"""Protected volume calculations."""

from __future__ import annotations

from src.engine.validators import validate_non_negative, validate_positive
from src.models.room import RoomInput


def calculate_area(length_m: float, width_m: float) -> float:
    validate_positive(length_m, "Largo")
    validate_positive(width_m, "Ancho")
    return length_m * width_m


def calculate_room_volume(length_m: float, width_m: float, height_m: float) -> float:
    validate_positive(height_m, "Alto")
    return calculate_area(length_m, width_m) * height_m


def calculate_raised_floor_volume(length_m: float, width_m: float, raised_floor_m: float) -> float:
    validate_non_negative(raised_floor_m, "Altura de piso técnico")
    return calculate_area(length_m, width_m) * raised_floor_m


def calculate_false_ceiling_volume(length_m: float, width_m: float, false_ceiling_m: float) -> float:
    validate_non_negative(false_ceiling_m, "Altura de cielo falso")
    return calculate_area(length_m, width_m) * false_ceiling_m


def calculate_gross_volume(room: RoomInput) -> float:
    if room.protect_raised_floor and room.raised_floor_m <= 0:
        raise ValueError("Para proteger el piso técnico debe ingresar una altura mayor que cero.")
    if room.protect_false_ceiling and room.false_ceiling_m <= 0:
        raise ValueError("Para proteger el cielo falso debe ingresar una altura mayor que cero.")
    return (
        calculate_room_volume(room.length_m, room.width_m, room.height_m)
        + (
            calculate_raised_floor_volume(room.length_m, room.width_m, room.raised_floor_m)
            if room.protect_raised_floor
            else 0.0
        )
        + (
            calculate_false_ceiling_volume(room.length_m, room.width_m, room.false_ceiling_m)
            if room.protect_false_ceiling
            else 0.0
        )
    )


def calculate_net_volume(room: RoomInput) -> float:
    validate_non_negative(room.structural_reductions_m3, "Reducciones estructurales")
    validate_non_negative(room.object_reductions_m3, "Reducciones por objetos")
    if room.object_reductions_m3 > 0 and not room.object_reductions_are_permanent:
        raise ValueError(
            "Solo pueden descontarse objetos sólidos, permanentes, no removibles y sin aberturas al recinto."
        )
    gross_volume = calculate_gross_volume(room)
    reductions = room.structural_reductions_m3 + room.object_reductions_m3
    if reductions > gross_volume:
        raise ValueError("Las reducciones no pueden superar el volumen bruto.")
    net_volume = gross_volume - reductions
    if net_volume <= 0:
        raise ValueError("El volumen neto debe ser mayor que cero.")
    return net_volume
