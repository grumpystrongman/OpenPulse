from __future__ import annotations

from datetime import datetime
from .base import circadian_hr, seeded_rng, ts_range


def generate(subject_id: str, start: datetime, periods: int, profile: str) -> list[dict]:
    rng = seeded_rng(subject_id, "oura")
    payloads: list[dict] = []
    for ts in ts_range(start, periods, 60):
        payloads.append(
            {
                "id": f"oura-{subject_id}-{int(ts.timestamp())}",
                "day": ts.date().isoformat(),
                "contributors": {"readiness": {"score": max(20, min(100, 72 + rng.randint(-20, 15)))}} ,
                "heart_rate": {"average": circadian_hr(ts.hour, profile) + rng.randint(-3, 3)},
                "hrv": {"rmssd": max(12, 48 + rng.randint(-18, 26))},
                "sleep": {"duration": max(18000, 26000 + rng.randint(-3500, 4200))},
                "temperature": {"deviation": round(rng.uniform(-0.8, 0.9), 2)},
            }
        )
    return payloads
