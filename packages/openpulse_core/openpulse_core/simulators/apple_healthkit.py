from __future__ import annotations

from datetime import datetime
from .base import circadian_hr, seeded_rng, ts_range


def generate(subject_id: str, start: datetime, periods: int, profile: str) -> list[dict]:
    rng = seeded_rng(subject_id, "apple_healthkit")
    payloads: list[dict] = []
    for ts in ts_range(start, periods, 15):
        hr = circadian_hr(ts.hour, profile) + rng.randint(-3, 4)
        payloads.append(
            {
                "uuid": f"hk-{subject_id}-{int(ts.timestamp())}",
                "type": "HKQuantityTypeIdentifierHeartRate",
                "startDate": ts.isoformat(),
                "endDate": ts.isoformat(),
                "value": hr,
                "unit": "count/min",
                "sourceRevision": {
                    "source": {"name": "Apple Watch", "bundleIdentifier": "com.apple.health"},
                    "version": "11.0",
                    "productType": "Watch7,4",
                },
                "metadata": {"HKWasUserEntered": False},
            }
        )
        if ts.hour == 7:
            payloads.append(
                {
                    "uuid": f"hk-hrv-{subject_id}-{int(ts.timestamp())}",
                    "type": "HKQuantityTypeIdentifierHeartRateVariabilitySDNN",
                    "startDate": ts.isoformat(),
                    "endDate": ts.isoformat(),
                    "value": float(rng.randint(28, 74)),
                    "unit": "ms",
                    "sourceRevision": {"source": {"name": "Apple Watch"}, "version": "11.0"},
                }
            )
    return payloads
