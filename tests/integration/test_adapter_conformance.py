import json
from datetime import datetime, timezone

import pytest

from openpulse_core.mappings import normalize_envelope
from openpulse_core.models import IngestEnvelope
from openpulse_core.synthetic import generate_payloads


@pytest.mark.parametrize(
    "manufacturer",
    [
        "apple_healthkit",
        "android_health_connect",
        "fitbit",
        "garmin",
        "oura",
        "whoop",
        "withings",
        "dexcom",
    ],
)
def test_adapter_conformance(manufacturer: str) -> None:
    payloads = generate_payloads(manufacturer, "sub-00001", days=1, profile="healthy")
    assert payloads, f"No payloads generated for {manufacturer}"
    envelope = IngestEnvelope(
        envelope_id=f"env-{manufacturer}",
        manufacturer=manufacturer,
        subject_id="sub-00001",
        connection_id=f"conn-{manufacturer}",
        idempotency_key=f"idem-{manufacturer}",
        received_time=datetime.now(tz=timezone.utc),
        source_payload=payloads[0],
    )
    result = normalize_envelope(envelope)
    assert len(result.observations) > 0
    assert all(obs.metric_code for obs in result.observations)


def test_sample_payloads_parse() -> None:
    files = [
        "sample-data/manufacturers/apple_healthkit.json",
        "sample-data/manufacturers/android_health_connect.json",
        "sample-data/manufacturers/fitbit.json",
        "sample-data/manufacturers/garmin.json",
        "sample-data/manufacturers/oura.json",
        "sample-data/manufacturers/whoop.json",
        "sample-data/manufacturers/withings.json",
        "sample-data/manufacturers/dexcom.json",
    ]
    for path in files:
        payload = json.loads(open(path, encoding="utf-8").read())
        assert isinstance(payload, dict)
