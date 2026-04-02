from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from hashlib import sha256
from uuid import uuid4

import httpx
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import ORJSONResponse, PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from redis import Redis

from openpulse_core.logging_utils import configure_logging
from openpulse_core.manufacturer_registry import CAPABILITY_REGISTRY
from openpulse_core.models import DeviceDescriptor, IngestEnvelope
from openpulse_core.security import validate_subject_id
from openpulse_data.kafka import get_producer
from openpulse_data.settings import settings

configure_logging("ingestion-gateway")
logger = logging.getLogger("openpulse.ingestion")

app = FastAPI(
    title="OpenPulse Ingestion Gateway",
    version="0.1.0",
    default_response_class=ORJSONResponse,
    description="REST/webhook gateway for OpenPulse manufacturer and partner ingest.",
)

redis_client = Redis(host=settings.redis_host, port=settings.redis_port, decode_responses=True)
producer = get_producer()

INGEST_COUNTER = Counter("openpulse_ingest_total", "Total ingested payloads", ["manufacturer", "status"])
INGEST_LATENCY = Histogram("openpulse_ingest_latency_seconds", "Ingestion request latency")
CONSENT_BASE_URL_ENV = "OPENPULSE_CONSENT_BASE_URL"
CONSENT_TIMEOUT_ENV = "OPENPULSE_CONSENT_TIMEOUT_SECONDS"
AUTH_TOKEN_ENV = "OPENPULSE_AUTH_TOKEN"


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "ingestion-gateway"}


@app.get("/metrics")
def metrics() -> PlainTextResponse:
    return PlainTextResponse(generate_latest().decode("utf-8"), media_type=CONTENT_TYPE_LATEST)


@app.post("/v1/ingest/{manufacturer}")
def ingest(
    manufacturer: str,
    request: Request,
    body: dict,
    x_subject_id: str = Header(...),
    x_connection_id: str = Header(...),
    x_idempotency_key: str = Header(...),
    x_device_id: str | None = Header(default=None),
    x_device_model: str | None = Header(default=None),
    x_device_firmware: str | None = Header(default=None),
    x_device_app_version: str | None = Header(default=None),
) -> dict:
    start = datetime.now(tz=timezone.utc)
    with INGEST_LATENCY.time():
        if manufacturer not in CAPABILITY_REGISTRY:
            INGEST_COUNTER.labels(manufacturer=manufacturer, status="rejected").inc()
            raise HTTPException(status_code=400, detail=f"Unsupported manufacturer: {manufacturer}")

        _rate_limit(request.client.host if request.client else "unknown")
        subject_id = validate_subject_id(x_subject_id)
        consent = _check_consent(subject_id=subject_id, manufacturer=manufacturer)
        if not consent["allowed"]:
            INGEST_COUNTER.labels(manufacturer=manufacturer, status="rejected").inc()
            logger.warning(
                "ingest.consent_denied",
                extra={
                    "manufacturer": manufacturer,
                    "subject_id": subject_id,
                    "connection_id": x_connection_id,
                    "reason": consent["reason"],
                },
            )
            raise HTTPException(status_code=403, detail={"reason": consent["reason"], "allowed": False})

        _enforce_idempotency(x_idempotency_key)

        envelope_id = uuid4().hex
        envelope = IngestEnvelope(
            envelope_id=envelope_id,
            manufacturer=manufacturer,
            subject_id=subject_id,
            connection_id=x_connection_id,
            idempotency_key=x_idempotency_key,
            received_time=start,
            source_payload=body,
            source_endpoint=str(request.url.path),
            device=DeviceDescriptor(
                device_id=x_device_id or f"{manufacturer}-unknown-device",
                manufacturer=manufacturer,
                model=x_device_model,
                firmware_version=x_device_firmware,
                app_version=x_device_app_version,
            ),
        )

        envelope_bytes = envelope.model_dump_json().encode("utf-8")
        producer.produce(
            settings.kafka_raw_topic,
            key=f"{manufacturer}:{subject_id}".encode("utf-8"),
            value=envelope_bytes,
            headers={
                "idempotency_key": x_idempotency_key,
                "consent_allowed": "true",
                "consent_reason": consent["reason"],
            },
        )
        producer.flush(5)

        INGEST_COUNTER.labels(manufacturer=manufacturer, status="accepted").inc()
        logger.info(
            "ingest.accepted",
            extra={
                "manufacturer": manufacturer,
                "subject_id": subject_id,
                "envelope_id": envelope_id,
                "connection_id": x_connection_id,
                "consent_reason": consent["reason"],
                "payload_hash": sha256(json.dumps(body, sort_keys=True).encode("utf-8")).hexdigest(),
            },
        )
        return {"status": "accepted", "envelope_id": envelope_id}


def _rate_limit(client_id: str, limit: int = 240) -> None:
    limit = int(os.getenv("OPENPULSE_INGEST_RATE_LIMIT_PER_MIN", "20000"))
    key = f"rate:{client_id}:{datetime.now(tz=timezone.utc):%Y%m%d%H%M}"
    current = redis_client.incr(key)
    if current == 1:
        redis_client.expire(key, 90)
    if current > limit:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")


def _check_consent(subject_id: str, manufacturer: str) -> dict[str, str | bool]:
    base_url = os.getenv(CONSENT_BASE_URL_ENV, "http://consent-identity-service:8004").rstrip("/")
    url = f"{base_url}/v1/consents/check/{subject_id}"
    params = {"scope": f"ingest:{manufacturer}"}
    headers = {"X-OpenPulse-Role": "integration"}
    token = os.getenv(AUTH_TOKEN_ENV)
    if token:
        headers["X-OpenPulse-Token"] = token
    try:
        timeout = float(os.getenv(CONSENT_TIMEOUT_ENV, "5"))
        with httpx.Client(timeout=timeout) as client:
            response = client.get(url, params=params, headers=headers)
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict):
                raise ValueError("Consent payload must be an object")
    except Exception as exc:  # noqa: BLE001
        logger.error(
            "ingest.consent_unavailable",
            extra={
                "subject_id": subject_id,
                "manufacturer": manufacturer,
                "consent_url": url,
                "error": str(exc),
            },
        )
        raise HTTPException(status_code=503, detail="Consent service unavailable") from exc

    allowed = bool(payload.get("allowed"))
    reason = str(payload.get("reason") or ("granted" if allowed else "denied"))
    if not allowed:
        return {"allowed": False, "reason": reason}
    return {"allowed": True, "reason": reason}


def _enforce_idempotency(idempotency_key: str) -> None:
    created = redis_client.set(name=f"idem:{idempotency_key}", value="1", ex=86400, nx=True)
    if not created:
        raise HTTPException(status_code=409, detail="Duplicate idempotency key")
