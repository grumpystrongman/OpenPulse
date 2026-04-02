from __future__ import annotations

from datetime import datetime
from .base import circadian_hr, seeded_rng, ts_range


def generate(subject_id: str, start: datetime, periods: int, profile: str) -> list[dict]:
    rng = seeded_rng(subject_id, "whoop")
    payloads: list[dict] = []
    for ts in ts_range(start, periods, 30):
        payloads.append(
            {
                "id": f"whoop-{subject_id}-{int(ts.timestamp())}",
                "cycle_id": int(ts.timestamp()),
                "start": ts.isoformat(),
                "recovery": {"score": max(1, min(100, 68 + rng.randint(-25, 20)))},
                "strain": {"score": round(max(0.0, min(21.0, 11 + rng.uniform(-5.5, 6.0))), 1)},
                "sleep": {"performance_pct": max(40, min(100, 82 + rng.randint(-30, 10))), "duration_milli": max(12000000, 26000000 + rng.randint(-6000000, 4000000))},
                "hr": {"resting": circadian_hr(ts.hour, profile) + rng.randint(-4, 5), "hrv_rmssd_milli": max(10, 45 + rng.randint(-15, 30))},
            }
        )
    return payloads
