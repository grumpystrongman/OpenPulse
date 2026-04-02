import json

from jsonschema import validate


def test_previous_schema_payload_still_valid() -> None:
    schema = json.loads(open("standards/schemas/json/openpulse-observation-1.0.0.schema.json", encoding="utf-8").read())
    payload = {
        "observation_id": "obs-legacy",
        "subject_id": "sub-legacy",
        "manufacturer": "fitbit",
        "metric_code": "heart_rate",
        "metric_display": "Heart Rate",
        "value": 66.0,
        "unit": "beats/min",
        "quality_score": 0.95,
        "completeness_score": 0.95,
        "confidence_score": 0.95,
        "clinical_grade": "consumer",
        "event_time": "2026-01-01T00:00:00Z"
    }
    validate(payload, schema)
