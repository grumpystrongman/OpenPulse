from __future__ import annotations

from datetime import datetime
from .base import circadian_hr, seeded_rng, ts_range


def generate(subject_id: str, start: datetime, periods: int, profile: str) -> list[dict]:
    rng = seeded_rng(subject_id, "garmin")
    payloads: list[dict] = []
    for ts in ts_range(start, periods, 15):
        payloads.append(
            {
                "userId": subject_id,
                "summaryStartTimeInSeconds": int(ts.timestamp()),
                "heartRate": circadian_hr(ts.hour, profile) + rng.randint(-4, 4),
                "stressLevel": max(0, min(100, 35 + rng.randint(-20, 30))),
                "spo2": max(88, min(100, 96 + rng.randint(-4, 2))),
                "bodyBattery": max(5, min(100, 62 + rng.randint(-25, 20))),
                "activeKilocalories": max(0, rng.randint(0, 45)),
                "steps": max(0, rng.randint(0, 140)),
                "device": {"product": "fenix 8", "firmware": "14.03"},
            }
        )
    return payloads
