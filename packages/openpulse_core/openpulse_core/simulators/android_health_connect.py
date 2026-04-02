from __future__ import annotations

from datetime import datetime
from .base import circadian_hr, seeded_rng, ts_range


def generate(subject_id: str, start: datetime, periods: int, profile: str) -> list[dict]:
    rng = seeded_rng(subject_id, "android_health_connect")
    payloads: list[dict] = []
    for ts in ts_range(start, periods, 30):
        payloads.append(
            {
                "recordType": "HeartRateRecord",
                "startTime": ts.isoformat(),
                "endTime": ts.isoformat(),
                "samples": [{"time": ts.isoformat(), "beatsPerMinute": circadian_hr(ts.hour, profile) + rng.randint(-5, 5)}],
                "metadata": {
                    "id": f"hc-{subject_id}-{int(ts.timestamp())}",
                    "dataOrigin": "com.google.android.apps.fitness",
                    "device": {"manufacturer": "Google", "model": "Pixel Watch 3"},
                },
            }
        )
    return payloads
