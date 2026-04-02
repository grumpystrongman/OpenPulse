from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import random
from typing import Iterable


def seeded_rng(subject_id: str, manufacturer: str) -> random.Random:
    digest = hashlib.sha256(f"{subject_id}:{manufacturer}".encode("utf-8")).hexdigest()
    return random.Random(int(digest[:16], 16))


def ts_range(start: datetime, periods: int, step_minutes: int) -> Iterable[datetime]:
    point = start.astimezone(timezone.utc)
    for _ in range(periods):
        yield point
        point += timedelta(minutes=step_minutes)


def circadian_hr(hour: int, profile: str) -> int:
    baseline = {"healthy": 66, "athletic": 56, "at_risk": 78, "chronic": 82}[profile]
    if 0 <= hour <= 5:
        baseline -= 7
    elif 18 <= hour <= 22:
        baseline += 8
    return baseline


def profile_glucose(profile: str) -> float:
    return {
        "healthy": 98.0,
        "athletic": 92.0,
        "at_risk": 122.0,
        "chronic": 155.0,
    }[profile]
