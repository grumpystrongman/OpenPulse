from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from hashlib import sha256
from uuid import uuid4

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import ORJSONResponse, PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from redis import Redis

from openpulse_core.logging_utils import configure_logging
from openpulse_core.manufacturer_registry import CAPABILITY_REGISTRY
from openpulse_core.models import DeviceDescriptor, IngestEnvelope
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
        _enforce_idempotency(x_idempotency_key)

        envelope_id = uuid4().hex
        envelope = IngestEnvelope(
            envelope_id=envelope_id,
            manufacturer=manufacturer,
            subject_id=x_subject_id,
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
            key=f"{manufacturer}:{x_subject_id}".encode("utf-8"),
            value=envelope_bytes,
            headers={"idempotency_key": x_idempotency_key},
        )
        producer.flush(5)

        INGEST_COUNTER.labels(manufacturer=manufacturer, status="accepted").inc()
        logger.info(
            "ingest.accepted",
            extra={
                "manufacturer": manufacturer,
                "subject_id": x_subject_id,
                "envelope_id": envelope_id,
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


def _enforce_idempotency(idempotency_key: str) -> None:
    created = redis_client.set(name=f"idem:{idempotency_key}", value="1", ex=86400, nx=True)
    if not created:
        raise HTTPException(status_code=409, detail="Duplicate idempotency key")
