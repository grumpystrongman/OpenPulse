from __future__ import annotations

from datetime import datetime
from .base import seeded_rng, ts_range


def generate(subject_id: str, start: datetime, periods: int, profile: str) -> list[dict]:
    rng = seeded_rng(subject_id, "withings")
    weight_base = {"healthy": 78.0, "athletic": 72.0, "at_risk": 92.0, "chronic": 98.0}[profile]
    payloads: list[dict] = []
    for ts in ts_range(start, periods, 360):
        weight = round(weight_base + rng.uniform(-1.3, 1.6), 2)
        payloads.append(
            {
                "userid": subject_id,
                "date": int(ts.timestamp()),
                "measuregrps": [
                    {
                        "grpid": int(ts.timestamp()),
                        "attrib": 0,
                        "date": int(ts.timestamp()),
                        "category": 1,
                        "measures": [
                            {"type": 1, "value": int(weight * 1000), "unit": -3},
                            {"type": 6, "value": int((24 + rng.uniform(-4, 7)) * 10), "unit": -1},
                            {"type": 9, "value": 110 + rng.randint(-10, 24), "unit": 0},
                            {"type": 10, "value": 72 + rng.randint(-8, 16), "unit": 0},
                        ],
                    }
                ],
            }
        )
    return payloads
