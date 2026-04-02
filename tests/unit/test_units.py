from openpulse_core.units import normalize_unit


def test_cal_to_kcal_conversion() -> None:
    assert normalize_unit(1200.0, "cal", "kcal") == 1.2


def test_lb_to_kg_conversion() -> None:
    kg = normalize_unit(200.0, "lb", "kg")
    assert round(kg, 6) == 90.718474
