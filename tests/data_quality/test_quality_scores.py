from datetime import datetime, timezone

from openpulse_core.mappings import normalize_envelope
from openpulse_core.models import IngestEnvelope


def test_quality_scores_within_bounds() -> None:
    envelope = IngestEnvelope(
        envelope_id="env-quality",
        manufacturer="dexcom",
        subject_id="sub-1",
        connection_id="conn-1",
        idempotency_key="idem-quality",
        received_time=datetime.now(tz=timezone.utc),
        source_payload={
            "recordId": "dex-1",
            "systemTime": "2026-03-01T06:00:00Z",
            "displayTime": "2026-03-01T06:00:00Z",
            "value": 144,
            "trend": "Flat",
            "unit": "mg/dL",
        },
    )
    result = normalize_envelope(envelope)
    assert result.observations
    for obs in result.observations:
        assert 0.0 <= obs.quality_score <= 1.0
        assert 0.0 <= obs.completeness_score <= 1.0
        assert 0.0 <= obs.confidence_score <= 1.0
