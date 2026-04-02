from __future__ import annotations

from datetime import datetime
from .base import circadian_hr, seeded_rng, ts_range


def generate(subject_id: str, start: datetime, periods: int, profile: str) -> list[dict]:
    rng = seeded_rng(subject_id, "fitbit")
    payloads: list[dict] = []
    for ts in ts_range(start, periods, 5):
        payloads.append(
            {
                "activities-heart-intraday": {
                    "datasetInterval": 1,
                    "datasetType": "minute",
                    "dataset": [{"time": ts.strftime("%H:%M:%S"), "value": circadian_hr(ts.hour, profile) + rng.randint(-4, 6)}],
                },
                "activities-steps-intraday": {
                    "datasetInterval": 1,
                    "datasetType": "minute",
                    "dataset": [{"time": ts.strftime("%H:%M:%S"), "value": max(0, rng.randint(-2, 18))}],
                },
                "dateTime": ts.date().isoformat(),
                "userId": subject_id,
                "deviceVersion": "Charge 6",
            }
        )
    return payloads
