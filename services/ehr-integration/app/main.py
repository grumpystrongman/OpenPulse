from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, Query
from fastapi.responses import ORJSONResponse, PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from openpulse_data.clickhouse import query

LOINC_MAP = {
    "heart_rate": "8867-4",
    "hrv_rmssd": "80404-7",
    "steps": "41950-7",
    "sleep_duration": "93832-4",
    "glucose": "2339-0",
    "blood_pressure_systolic": "8480-6",
    "blood_pressure_diastolic": "8462-4",
    "spo2": "59408-5",
}

app = FastAPI(
    title="OpenPulse EHR Integration",
    version="0.1.0",
    default_response_class=ORJSONResponse,
    description="FHIR-aligned export and EHR integration package endpoints.",
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "ehr-integration", "timestamp": datetime.now(tz=timezone.utc).isoformat()}


@app.get("/metrics")
def metrics() -> PlainTextResponse:
    return PlainTextResponse(generate_latest().decode("utf-8"), media_type=CONTENT_TYPE_LATEST)


@app.get("/v1/fhir/observations/{subject_id}")
def export_fhir_observations(
    subject_id: str,
    limit: int = Query(default=500, ge=1, le=5000),
) -> dict[str, list[dict[str, Any]]]:
    rows = query(
        f"""
        SELECT observation_id, metric_code, metric_display, value, unit, event_time, manufacturer, quality_score
        FROM openpulse.observation
        WHERE subject_id = '{subject_id}'
        ORDER BY event_time DESC
        LIMIT {limit}
        """
    )
    bundle = [_to_fhir_observation(subject_id, row) for row in rows]
    return {"resourceType": "Bundle", "type": "collection", "entry": [{"resource": item} for item in bundle]}


@app.get("/v1/export/bulk")
def bulk_export(metric_code: str | None = None, days: int = 30) -> dict:
    predicate = "1=1" if not metric_code else f"metric_code = '{metric_code}'"
    rows = query(
        f"""
        SELECT subject_id, metric_code, event_time, value, unit, manufacturer, observation_id
        FROM openpulse.observation
        WHERE {predicate}
          AND event_time >= now() - INTERVAL {days} DAY
        ORDER BY event_time DESC
        """
    )
    return {
        "records": rows,
        "exported_at": datetime.now(tz=timezone.utc).isoformat(),
        "record_count": len(rows),
    }


def _to_fhir_observation(subject_id: str, row: dict[str, Any]) -> dict[str, Any]:
    metric_code = row["metric_code"]
    loinc = LOINC_MAP.get(metric_code, "72166-2")
    return {
        "resourceType": "Observation",
        "id": row["observation_id"],
        "status": "final",
        "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "activity"}]}],
        "code": {
            "coding": [
                {
                    "system": "http://loinc.org",
                    "code": loinc,
                    "display": row["metric_display"],
                }
            ],
            "text": row["metric_display"],
        },
        "subject": {"reference": f"Patient/{subject_id}"},
        "effectiveDateTime": row["event_time"],
        "valueQuantity": {
            "value": row["value"],
            "unit": row["unit"],
            "system": "http://unitsofmeasure.org",
            "code": row["unit"],
        },
        "extension": [
            {
                "url": "https://openpulse.dev/fhir/StructureDefinition/source-manufacturer",
                "valueString": row["manufacturer"],
            },
            {
                "url": "https://openpulse.dev/fhir/StructureDefinition/data-quality-score",
                "valueDecimal": row["quality_score"],
            },
        ],
    }
