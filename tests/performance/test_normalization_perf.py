import time
from datetime import datetime, timezone

from openpulse_core.mappings import normalize_envelope
from openpulse_core.models import IngestEnvelope
from openpulse_core.synthetic import generate_payloads


def test_normalization_performance() -> None:
    payloads = generate_payloads("fitbit", "sub-load", days=7, profile="healthy")[:2000]
    start = time.perf_counter()
    for i, payload in enumerate(payloads):
        envelope = IngestEnvelope(
            envelope_id=f"env-perf-{i}",
            manufacturer="fitbit",
            subject_id="sub-load",
            connection_id="conn-load",
            idempotency_key=f"idem-perf-{i}",
            received_time=datetime.now(tz=timezone.utc),
            source_payload=payload,
        )
        result = normalize_envelope(envelope)
        assert result.observations
    elapsed = time.perf_counter() - start
    assert elapsed < 12.0
