from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from typing import Any

from dateutil import parser as dateparser

from .models import CanonicalObservation, IngestEnvelope, NormalizationResult, ProvenanceLink
from .taxonomy import METRIC_TAXONOMY
from .units import normalize_unit


def normalize_envelope(envelope: IngestEnvelope, mapping_version: str = "1.0.0") -> NormalizationResult:
    manufacturer = envelope.manufacturer
    payload = envelope.source_payload
    observations: list[CanonicalObservation] = []
    rejected: list[dict[str, Any]] = []

    try:
        if manufacturer == "apple_healthkit":
            observations.extend(_map_apple(envelope, payload))
        elif manufacturer == "android_health_connect":
            observations.extend(_map_android(envelope, payload))
        elif manufacturer == "fitbit":
            observations.extend(_map_fitbit(envelope, payload))
        elif manufacturer == "garmin":
            observations.extend(_map_garmin(envelope, payload))
        elif manufacturer == "oura":
            observations.extend(_map_oura(envelope, payload))
        elif manufacturer == "whoop":
            observations.extend(_map_whoop(envelope, payload))
        elif manufacturer == "withings":
            observations.extend(_map_withings(envelope, payload))
        elif manufacturer == "dexcom":
            observations.extend(_map_dexcom(envelope, payload))
        else:
            rejected.append({"reason": "unsupported_manufacturer", "payload": payload})
    except Exception as exc:  # noqa: BLE001
        rejected.append({"reason": str(exc), "payload": payload})

    payload_hash = hashlib.sha256(str(payload).encode("utf-8")).hexdigest()
    provenance = [
        ProvenanceLink(
            observation_id=o.observation_id,
            envelope_id=envelope.envelope_id,
            payload_hash=payload_hash,
            manufacturer=manufacturer,
            mapping_version=mapping_version,
        )
        for o in observations
    ]
    return NormalizationResult(
        envelope_id=envelope.envelope_id,
        observations=observations,
        provenance=provenance,
        rejected_records=rejected,
    )


def _obs(
    envelope: IngestEnvelope,
    metric_code: str,
    value: float | None,
    event_time: datetime,
    *,
    unit: str | None = None,
    original_value: float | None = None,
    original_unit: str | None = None,
    value_text: str | None = None,
    extension_payload: dict[str, Any] | None = None,
    quality_score: float = 0.95,
    clinical_grade: str = "consumer",
) -> CanonicalObservation:
    metric_meta = METRIC_TAXONOMY[metric_code]
    canonical_unit = metric_meta["canonical_unit"]
    normalized_value: float | None = value
    if value is not None and unit and canonical_unit != "stage" and canonical_unit != "phase" and unit != canonical_unit:
        normalized_value = round(normalize_unit(value, unit, canonical_unit), 6)
    obs_id = hashlib.sha256(
        f"{envelope.envelope_id}:{metric_code}:{event_time.isoformat()}:{value_text or normalized_value}".encode("utf-8")
    ).hexdigest()[:24]
    return CanonicalObservation(
        observation_id=obs_id,
        subject_id=envelope.subject_id,
        manufacturer=envelope.manufacturer,
        metric_code=metric_code,
        metric_display=metric_meta["display"],
        value=normalized_value,
        value_text=value_text,
        unit=canonical_unit if canonical_unit not in {"stage", "phase"} else None,
        original_value=original_value if original_value is not None else value,
        original_unit=original_unit if original_unit is not None else unit,
        quality_score=quality_score,
        completeness_score=0.98,
        confidence_score=0.96,
        clinical_grade=clinical_grade,  # type: ignore[arg-type]
        event_time=event_time,
        observed_time=event_time,
        device_time=event_time,
        received_time=envelope.received_time,
        processed_time=datetime.now(tz=timezone.utc),
        extension_namespace=f"openpulse.ext.{envelope.manufacturer}",
        extension_payload=extension_payload,
    )


def _parse(ts: str) -> datetime:
    return dateparser.isoparse(ts).astimezone(timezone.utc)


def _map_apple(envelope: IngestEnvelope, payload: dict[str, Any]) -> list[CanonicalObservation]:
    ts = _parse(payload["startDate"])
    metric = payload["type"]
    if "HeartRateVariability" in metric:
        return [_obs(envelope, "hrv_rmssd", float(payload["value"]), ts, unit=payload.get("unit", "ms"))]
    if "HeartRate" in metric:
        return [_obs(envelope, "heart_rate", float(payload["value"]), ts, unit="beats/min")]
    return []


def _map_android(envelope: IngestEnvelope, payload: dict[str, Any]) -> list[CanonicalObservation]:
    sample = payload["samples"][0]
    ts = _parse(sample["time"])
    return [_obs(envelope, "heart_rate", float(sample["beatsPerMinute"]), ts, unit="beats/min")]


def _map_fitbit(envelope: IngestEnvelope, payload: dict[str, Any]) -> list[CanonicalObservation]:
    base_date = payload["dateTime"]
    hr_sample = payload["activities-heart-intraday"]["dataset"][0]
    ts = _parse(f"{base_date}T{hr_sample['time']}Z")
    steps_sample = payload["activities-steps-intraday"]["dataset"][0]
    return [
        _obs(envelope, "heart_rate", float(hr_sample["value"]), ts, unit="beats/min"),
        _obs(envelope, "steps", float(steps_sample["value"]), ts, unit="count"),
    ]


def _map_garmin(envelope: IngestEnvelope, payload: dict[str, Any]) -> list[CanonicalObservation]:
    ts = datetime.fromtimestamp(payload["summaryStartTimeInSeconds"], tz=timezone.utc)
    return [
        _obs(envelope, "heart_rate", float(payload["heartRate"]), ts, unit="beats/min"),
        _obs(envelope, "stress_score", float(payload["stressLevel"]), ts, unit="score"),
        _obs(envelope, "spo2", float(payload["spo2"]), ts, unit="%"),
        _obs(envelope, "body_battery", float(payload["bodyBattery"]), ts, unit="score"),
        _obs(envelope, "steps", float(payload["steps"]), ts, unit="count"),
    ]


def _map_oura(envelope: IngestEnvelope, payload: dict[str, Any]) -> list[CanonicalObservation]:
    ts = _parse(f"{payload['day']}T08:00:00Z")
    return [
        _obs(envelope, "readiness_score", float(payload["contributors"]["readiness"]["score"]), ts, unit="score"),
        _obs(envelope, "heart_rate", float(payload["heart_rate"]["average"]), ts, unit="beats/min"),
        _obs(envelope, "hrv_rmssd", float(payload["hrv"]["rmssd"]), ts, unit="ms"),
        _obs(envelope, "sleep_duration", float(payload["sleep"]["duration"]) / 60.0, ts, unit="min"),
        _obs(
            envelope,
            "skin_temperature",
            float(payload["temperature"]["deviation"]),
            ts,
            unit="degC",
            extension_payload={"deviation": payload["temperature"]["deviation"]},
        ),
    ]


def _map_whoop(envelope: IngestEnvelope, payload: dict[str, Any]) -> list[CanonicalObservation]:
    ts = _parse(payload["start"])
    return [
        _obs(envelope, "recovery_score", float(payload["recovery"]["score"]), ts, unit="score"),
        _obs(envelope, "strain_score", float(payload["strain"]["score"]), ts, unit="score"),
        _obs(envelope, "sleep_duration", float(payload["sleep"]["duration_milli"]) / 60000.0, ts, unit="min"),
        _obs(envelope, "heart_rate", float(payload["hr"]["resting"]), ts, unit="beats/min"),
        _obs(envelope, "hrv_rmssd", float(payload["hr"]["hrv_rmssd_milli"]), ts, unit="ms"),
    ]


def _map_withings(envelope: IngestEnvelope, payload: dict[str, Any]) -> list[CanonicalObservation]:
    ts = datetime.fromtimestamp(payload["date"], tz=timezone.utc)
    observations: list[CanonicalObservation] = []
    for measure in payload["measuregrps"][0]["measures"]:
        metric_type = int(measure["type"])
        raw_value = float(measure["value"]) * (10 ** int(measure["unit"]))
        if metric_type == 1:
            observations.append(_obs(envelope, "body_weight", raw_value, ts, unit="kg"))
        elif metric_type == 6:
            observations.append(_obs(envelope, "body_fat_percent", raw_value, ts, unit="%"))
        elif metric_type == 9:
            observations.append(_obs(envelope, "blood_pressure_systolic", raw_value, ts, unit="mmHg", clinical_grade="clinical"))
        elif metric_type == 10:
            observations.append(_obs(envelope, "blood_pressure_diastolic", raw_value, ts, unit="mmHg", clinical_grade="clinical"))
    return observations


def _map_dexcom(envelope: IngestEnvelope, payload: dict[str, Any]) -> list[CanonicalObservation]:
    ts = _parse(payload["systemTime"])
    return [
        _obs(
            envelope,
            "glucose",
            float(payload["value"]),
            ts,
            unit=payload.get("unit", "mg/dL"),
            clinical_grade="clinical",
            extension_payload={"trend": payload.get("trend")},
            quality_score=0.99,
        )
    ]
