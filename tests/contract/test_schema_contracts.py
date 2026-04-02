import json
from datetime import datetime, timezone

from jsonschema import validate

from openpulse_core.mappings import normalize_envelope
from openpulse_core.models import IngestEnvelope


def test_envelope_contract_schema() -> None:
    schema = json.loads(open("standards/schemas/json/ingest-envelope-1.0.0.schema.json", encoding="utf-8").read())
    envelope = IngestEnvelope(
        envelope_id="env-1",
        manufacturer="fitbit",
        subject_id="sub-1",
        connection_id="conn-1",
        idempotency_key="idem-1",
        received_time=datetime.now(tz=timezone.utc),
        source_payload=json.loads(open("sample-data/manufacturers/fitbit.json", encoding="utf-8").read()),
    )
    validate(envelope.model_dump(mode="json"), schema)


def test_observation_contract_schema() -> None:
    schema = json.loads(open("standards/schemas/json/openpulse-observation-1.0.0.schema.json", encoding="utf-8").read())
    envelope = IngestEnvelope(
        envelope_id="env-2",
        manufacturer="dexcom",
        subject_id="sub-1",
        connection_id="conn-1",
        idempotency_key="idem-2",
        received_time=datetime.now(tz=timezone.utc),
        source_payload=json.loads(open("sample-data/manufacturers/dexcom.json", encoding="utf-8").read()),
    )
    result = normalize_envelope(envelope)
    assert result.observations
    validate(result.observations[0].model_dump(mode="json"), schema)
