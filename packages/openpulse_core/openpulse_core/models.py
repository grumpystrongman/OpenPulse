from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

TimeSemantics = Literal[
    "event_time",
    "observed_time",
    "device_time",
    "received_time",
    "processed_time",
]


class DeviceDescriptor(BaseModel):
    device_id: str
    manufacturer: str
    model: str | None = None
    firmware_version: str | None = None
    app_version: str | None = None


class IngestEnvelope(BaseModel):
    envelope_id: str
    manufacturer: str
    subject_id: str
    connection_id: str
    idempotency_key: str
    received_time: datetime
    source_payload: dict[str, Any]
    device: DeviceDescriptor | None = None
    source_endpoint: str | None = None


class CanonicalObservation(BaseModel):
    observation_id: str
    subject_id: str
    manufacturer: str
    metric_code: str
    metric_display: str
    value: float | None = None
    value_text: str | None = None
    unit: str | None = None
    original_value: float | None = None
    original_unit: str | None = None
    quality_score: float = Field(default=1.0, ge=0, le=1)
    completeness_score: float = Field(default=1.0, ge=0, le=1)
    confidence_score: float = Field(default=1.0, ge=0, le=1)
    clinical_grade: Literal["consumer", "clinical"] = "consumer"
    event_time: datetime
    observed_time: datetime | None = None
    device_time: datetime | None = None
    received_time: datetime | None = None
    processed_time: datetime | None = None
    session_id: str | None = None
    extension_namespace: str | None = None
    extension_payload: dict[str, Any] | None = None


class ProvenanceLink(BaseModel):
    observation_id: str
    envelope_id: str
    payload_hash: str
    manufacturer: str
    mapping_version: str


class NormalizationResult(BaseModel):
    envelope_id: str
    observations: list[CanonicalObservation]
    provenance: list[ProvenanceLink]
    rejected_records: list[dict[str, Any]] = Field(default_factory=list)
