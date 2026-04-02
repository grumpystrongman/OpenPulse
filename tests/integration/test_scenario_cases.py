from datetime import datetime, timezone

import pytest

from openpulse_core.mappings import normalize_envelope
from openpulse_core.models import IngestEnvelope


@pytest.mark.parametrize(
    "manufacturer,payload,expected_metric",
    [
        (
            "apple_healthkit",
            {
                "uuid": "apple-1",
                "type": "HKQuantityTypeIdentifierHeartRateVariabilitySDNN",
                "startDate": "2026-03-01T06:00:00Z",
                "endDate": "2026-03-01T06:00:00Z",
                "value": 42,
                "unit": "ms",
            },
            "hrv_rmssd",
        ),
        (
            "garmin",
            {
                "userId": "sub-1",
                "summaryStartTimeInSeconds": 1772344800,
                "heartRate": 68,
                "stressLevel": 44,
                "spo2": 97,
                "bodyBattery": 68,
                "activeKilocalories": 30,
                "steps": 100,
            },
            "stress_score",
        ),
        (
            "oura",
            {
                "id": "oura-1",
                "day": "2026-03-01",
                "contributors": {"readiness": {"score": 80}},
                "heart_rate": {"average": 59},
                "hrv": {"rmssd": 55},
                "sleep": {"duration": 26400},
                "temperature": {"deviation": 0.1},
            },
            "readiness_score",
        ),
    ],
)
def test_realistic_scenario_payloads(manufacturer: str, payload: dict, expected_metric: str) -> None:
    envelope = IngestEnvelope(
        envelope_id=f"env-{manufacturer}",
        manufacturer=manufacturer,
        subject_id="sub-1",
        connection_id=f"conn-{manufacturer}",
        idempotency_key=f"idem-{manufacturer}",
        received_time=datetime.now(tz=timezone.utc),
        source_payload=payload,
    )
    result = normalize_envelope(envelope)
    assert any(obs.metric_code == expected_metric for obs in result.observations)
