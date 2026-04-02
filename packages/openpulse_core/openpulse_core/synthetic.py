from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Callable

from .simulators import (
    android_health_connect,
    apple_healthkit,
    dexcom,
    fitbit,
    garmin,
    oura,
    whoop,
    withings,
)

Generator = Callable[[str, datetime, int, str], list[dict]]

GENERATORS: dict[str, Generator] = {
    "apple_healthkit": apple_healthkit.generate,
    "android_health_connect": android_health_connect.generate,
    "fitbit": fitbit.generate,
    "garmin": garmin.generate,
    "oura": oura.generate,
    "whoop": whoop.generate,
    "withings": withings.generate,
    "dexcom": dexcom.generate,
}


def generate_payloads(
    manufacturer: str,
    subject_id: str,
    days: int = 1,
    profile: str = "healthy",
    cadence_minutes: int | None = None,
) -> list[dict]:
    if manufacturer not in GENERATORS:
        raise ValueError(f"Unsupported manufacturer {manufacturer}")
    start = datetime.now(tz=timezone.utc) - timedelta(days=days)
    periods = max(1, int((days * 24 * 60) / (cadence_minutes or _default_cadence(manufacturer))))
    return GENERATORS[manufacturer](subject_id, start, periods, profile)


def _default_cadence(manufacturer: str) -> int:
    return {
        "apple_healthkit": 15,
        "android_health_connect": 30,
        "fitbit": 5,
        "garmin": 15,
        "oura": 60,
        "whoop": 30,
        "withings": 360,
        "dexcom": 5,
    }[manufacturer]
