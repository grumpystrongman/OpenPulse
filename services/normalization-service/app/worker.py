from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from hashlib import sha256
from uuid import uuid4

from confluent_kafka import KafkaError

from openpulse_core.logging_utils import configure_logging
from openpulse_core.mappings import normalize_envelope
from openpulse_core.models import IngestEnvelope
from openpulse_data.clickhouse import insert_rows
from openpulse_data.kafka import get_consumer, get_producer
from openpulse_data.settings import settings
from openpulse_data.storage import BronzeStorage

configure_logging("normalization-service")
logger = logging.getLogger("openpulse.normalization")


def run() -> None:
    consumer = get_consumer("openpulse-normalization", [settings.kafka_raw_topic])
    producer = get_producer()
    storage = BronzeStorage()

    while True:
        message = consumer.poll(1.0)
        if message is None:
            continue
        if message.error():
            if message.error().code() == KafkaError._PARTITION_EOF:
                continue
            logger.error("kafka_error", extra={"error": str(message.error())})
            continue

        started = datetime.now(tz=timezone.utc)
        run_id = uuid4().hex
        raw_value = message.value().decode("utf-8")
        try:
            envelope = IngestEnvelope.model_validate_json(raw_value)
            bronze_uri = storage.put_json(envelope.manufacturer, envelope.envelope_id, raw_value.encode("utf-8"))

            insert_rows(
                "source_payload",
                [
                    {
                        "envelope_id": envelope.envelope_id,
                        "manufacturer": envelope.manufacturer,
                        "subject_id": envelope.subject_id,
                        "connection_id": envelope.connection_id,
                        "idempotency_key": envelope.idempotency_key,
                        "received_time": envelope.received_time,
                        "source_endpoint": envelope.source_endpoint,
                        "payload_json": json.dumps(envelope.source_payload),
                        "payload_hash": sha256(json.dumps(envelope.source_payload, sort_keys=True).encode("utf-8")).hexdigest(),
                        "bronze_uri": bronze_uri,
                    }
                ],
            )

            result = normalize_envelope(envelope)
            obs_rows = [
                {
                    "observation_id": o.observation_id,
                    "envelope_id": envelope.envelope_id,
                    "subject_id": o.subject_id,
                    "manufacturer": o.manufacturer,
                    "metric_code": o.metric_code,
                    "metric_display": o.metric_display,
                    "value": o.value,
                    "value_text": o.value_text,
                    "unit": o.unit,
                    "original_value": o.original_value,
                    "original_unit": o.original_unit,
                    "quality_score": o.quality_score,
                    "completeness_score": o.completeness_score,
                    "confidence_score": o.confidence_score,
                    "clinical_grade": o.clinical_grade,
                    "event_time": o.event_time,
                    "observed_time": o.observed_time,
                    "device_time": o.device_time,
                    "received_time": o.received_time,
                    "processed_time": o.processed_time,
                    "session_id": o.session_id,
                    "extension_namespace": o.extension_namespace,
                    "extension_payload_json": json.dumps(o.extension_payload) if o.extension_payload else None,
                }
                for o in result.observations
            ]
            insert_rows("observation", obs_rows)

            prov_rows = [
                {
                    "observation_id": p.observation_id,
                    "envelope_id": p.envelope_id,
                    "payload_hash": p.payload_hash,
                    "manufacturer": p.manufacturer,
                    "mapping_version": p.mapping_version,
                    "linked_at": datetime.now(tz=timezone.utc),
                }
                for p in result.provenance
            ]
            insert_rows("provenance_link", prov_rows)

            quality_rows = [
                {
                    "quality_assessment_id": uuid4().hex,
                    "envelope_id": envelope.envelope_id,
                    "observation_id": o.observation_id,
                    "score": (o.quality_score + o.completeness_score + o.confidence_score) / 3,
                    "dimensions_json": json.dumps(
                        {
                            "quality": o.quality_score,
                            "completeness": o.completeness_score,
                            "confidence": o.confidence_score,
                        }
                    ),
                    "assessed_at": datetime.now(tz=timezone.utc),
                }
                for o in result.observations
            ]
            insert_rows("quality_assessment", quality_rows)
            _upsert_domain_tables(result.observations)

            insert_rows(
                "normalization_run",
                [
                    {
                        "run_id": run_id,
                        "envelope_id": envelope.envelope_id,
                        "manufacturer": envelope.manufacturer,
                        "status": "success",
                        "started_at": started,
                        "ended_at": datetime.now(tz=timezone.utc),
                        "records_in": 1,
                        "records_out": len(result.observations),
                        "rejected": len(result.rejected_records),
                        "notes": "",
                    }
                ],
            )

            for obs in result.observations:
                producer.produce(
                    settings.kafka_normalized_topic,
                    key=f"{obs.subject_id}:{obs.metric_code}".encode("utf-8"),
                    value=obs.model_dump_json().encode("utf-8"),
                )
            producer.flush(5)
            consumer.commit(message)
        except Exception as exc:  # noqa: BLE001
            logger.exception("normalization_failed", extra={"error": str(exc)})
            insert_rows(
                "failed_record_queue",
                [
                    {
                        "failed_id": uuid4().hex,
                        "envelope_json": raw_value,
                        "error_message": str(exc),
                        "failed_at": datetime.now(tz=timezone.utc),
                        "replay_status": "pending",
                        "replayed_at": None,
                    }
                ],
            )
            insert_rows(
                "normalization_run",
                [
                    {
                        "run_id": run_id,
                        "envelope_id": "unknown",
                        "manufacturer": "unknown",
                        "status": "failed",
                        "started_at": started,
                        "ended_at": datetime.now(tz=timezone.utc),
                        "records_in": 1,
                        "records_out": 0,
                        "rejected": 1,
                        "notes": str(exc),
                    }
                ],
            )
            consumer.commit(message)


def _upsert_domain_tables(observations) -> None:  # type: ignore[no-untyped-def]
    glucose_rows = []
    body_rows = {}
    bp_rows = {}
    recovery_rows = {}

    for obs in observations:
        key = (obs.subject_id, obs.event_time)
        if obs.metric_code == "glucose":
            glucose_rows.append(
                {
                    "glucose_reading_id": uuid4().hex,
                    "subject_id": obs.subject_id,
                    "manufacturer": obs.manufacturer,
                    "event_time": obs.event_time,
                    "glucose_mg_dl": obs.value,
                    "trend": (obs.extension_payload or {}).get("trend") if obs.extension_payload else None,
                    "clinical_grade": obs.clinical_grade,
                    "source_observation_id": obs.observation_id,
                }
            )
        if obs.metric_code in {"body_weight", "body_fat_percent"}:
            body = body_rows.setdefault(
                key,
                {
                    "body_measurement_id": uuid4().hex,
                    "subject_id": obs.subject_id,
                    "manufacturer": obs.manufacturer,
                    "event_time": obs.event_time,
                    "body_weight_kg": None,
                    "body_fat_percent": None,
                    "source_observation_ids": [],
                },
            )
            if obs.metric_code == "body_weight":
                body["body_weight_kg"] = obs.value
            if obs.metric_code == "body_fat_percent":
                body["body_fat_percent"] = obs.value
            body["source_observation_ids"].append(obs.observation_id)
        if obs.metric_code in {"blood_pressure_systolic", "blood_pressure_diastolic"}:
            bp = bp_rows.setdefault(
                key,
                {
                    "blood_pressure_id": uuid4().hex,
                    "subject_id": obs.subject_id,
                    "manufacturer": obs.manufacturer,
                    "event_time": obs.event_time,
                    "systolic_mmhg": None,
                    "diastolic_mmhg": None,
                    "source_observation_ids": [],
                },
            )
            if obs.metric_code == "blood_pressure_systolic":
                bp["systolic_mmhg"] = obs.value
            if obs.metric_code == "blood_pressure_diastolic":
                bp["diastolic_mmhg"] = obs.value
            bp["source_observation_ids"].append(obs.observation_id)
        if obs.metric_code in {"recovery_score", "readiness_score", "strain_score", "stress_score"}:
            rec = recovery_rows.setdefault(
                key,
                {
                    "recovery_id": uuid4().hex,
                    "subject_id": obs.subject_id,
                    "manufacturer": obs.manufacturer,
                    "event_time": obs.event_time,
                    "recovery_score": None,
                    "readiness_score": None,
                    "strain_score": None,
                    "stress_score": None,
                    "source_observation_ids": [],
                },
            )
            rec[obs.metric_code] = obs.value
            rec["source_observation_ids"].append(obs.observation_id)

    insert_rows("glucose_reading", glucose_rows)
    insert_rows("body_measurement", list(body_rows.values()))
    insert_rows("blood_pressure_reading", list(bp_rows.values()))
    insert_rows("recovery_state", list(recovery_rows.values()))


if __name__ == "__main__":
    run()
