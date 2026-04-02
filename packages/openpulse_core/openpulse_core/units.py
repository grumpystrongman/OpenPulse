from __future__ import annotations

UNIT_CONVERSIONS: dict[tuple[str, str], float] = {
    ("cal", "kcal"): 0.001,
    ("F", "degC"): 5 / 9,
    ("lb", "kg"): 0.45359237,
    ("mmol/L", "mg/dL"): 18.0,
}


def normalize_unit(value: float, original_unit: str, canonical_unit: str) -> float:
    if original_unit == canonical_unit:
        return value
    key = (original_unit, canonical_unit)
    if key not in UNIT_CONVERSIONS:
        raise ValueError(f"Unsupported conversion {original_unit} -> {canonical_unit}")
    factor = UNIT_CONVERSIONS[key]
    if key == ("F", "degC"):
        return (value - 32.0) * factor
    return value * factor
