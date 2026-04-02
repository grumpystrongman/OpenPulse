from __future__ import annotations

from datetime import datetime
from .base import profile_glucose, seeded_rng, ts_range


def generate(subject_id: str, start: datetime, periods: int, profile: str) -> list[dict]:
    rng = seeded_rng(subject_id, "dexcom")
    base_glucose = profile_glucose(profile)
    payloads: list[dict] = []
    for ts in ts_range(start, periods, 5):
        payloads.append(
            {
                "recordId": f"dex-{subject_id}-{int(ts.timestamp())}",
                "systemTime": ts.isoformat(),
                "displayTime": ts.isoformat(),
                "value": int(max(55, base_glucose + rng.uniform(-26, 34))),
                "trend": rng.choice(["Flat", "FortyFiveUp", "FortyFiveDown", "SingleUp", "SingleDown"]),
                "unit": "mg/dL",
                "realtimeValue": True,
            }
        )
    return payloads
