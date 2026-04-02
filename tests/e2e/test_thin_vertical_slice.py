from datetime import datetime, timezone

from openpulse_core.mappings import normalize_envelope
from openpulse_core.models import IngestEnvelope
from openpulse_core.synthetic import generate_payloads


def test_vertical_slice_fitbit() -> None:
    payload = generate_payloads("fitbit", "sub-00100", days=1, profile="athletic")[0]
    envelope = IngestEnvelope(
        envelope_id="env-fitbit-vslice",
        manufacturer="fitbit",
        subject_id="sub-00100",
        connection_id="conn-fitbit-sub-00100",
        idempotency_key="idem-fitbit-vslice",
        received_time=datetime.now(tz=timezone.utc),
        source_payload=payload,
    )
    result = normalize_envelope(envelope)
    assert result.observations
    assert any(o.metric_code == "heart_rate" for o in result.observations)
    assert any(o.metric_code == "steps" for o in result.observations)
    assert len(result.provenance) == len(result.observations)
