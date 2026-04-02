from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import uuid4

import httpx
from fastapi import BackgroundTasks, FastAPI, HTTPException, Query
from fastapi.responses import ORJSONResponse
from fastapi.responses import PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, Counter, generate_latest

from openpulse_core.logging_utils import configure_logging
from openpulse_core.manufacturer_registry import CAPABILITY_REGISTRY
from openpulse_core.synthetic import generate_payloads

configure_logging("connector-service")
logger = logging.getLogger("openpulse.connector")

app = FastAPI(
    title="OpenPulse Connector Service",
    version="0.1.0",
    default_response_class=ORJSONResponse,
    description="Manufacturer adapters and synthetic connector orchestration.",
)

PUSH_COUNTER = Counter("openpulse_connector_push_total", "Connector payload pushes", ["manufacturer", "status"])
INGESTION_URL = "http://ingestion-gateway:8001"


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "connector-service"}


@app.get("/metrics")
def metrics() -> PlainTextResponse:
    return PlainTextResponse(generate_latest().decode("utf-8"), media_type=CONTENT_TYPE_LATEST)


@app.get("/v1/connectors/capabilities")
def capabilities() -> list[dict]:
    return [
        {
            "manufacturer": capability.manufacturer,
            "auth_model": capability.auth_model,
            "ingestion_mode": capability.ingestion_mode,
            "supported_metrics": capability.supported_metrics,
            "update_frequency": capability.update_frequency,
            "quirks": capability.quirks,
        }
        for capability in CAPABILITY_REGISTRY.values()
    ]


@app.post("/v1/simulate/{manufacturer}")
async def simulate(
    manufacturer: str,
    background_tasks: BackgroundTasks,
    subjects: int = Query(default=2, ge=1, le=500),
    days: int = Query(default=2, ge=1, le=365),
    profile: str = Query(default="healthy", pattern="^(healthy|athletic|at_risk|chronic)$"),
) -> dict:
    if manufacturer not in CAPABILITY_REGISTRY:
        raise HTTPException(status_code=400, detail=f"Unsupported manufacturer: {manufacturer}")
    run_id = uuid4().hex
    background_tasks.add_task(_run_simulation, manufacturer, subjects, days, profile, run_id)
    return {"status": "started", "run_id": run_id, "manufacturer": manufacturer}


@app.post("/v1/simulate/all")
async def simulate_all(
    background_tasks: BackgroundTasks,
    subjects: int = Query(default=2, ge=1, le=500),
    days: int = Query(default=2, ge=1, le=365),
    profile: str = Query(default="healthy", pattern="^(healthy|athletic|at_risk|chronic)$"),
) -> dict:
    run_id = uuid4().hex
    for manufacturer in CAPABILITY_REGISTRY:
        background_tasks.add_task(_run_simulation, manufacturer, subjects, days, profile, run_id)
    return {"status": "started", "run_id": run_id, "manufacturers": list(CAPABILITY_REGISTRY.keys())}


async def _run_simulation(manufacturer: str, subjects: int, days: int, profile: str, run_id: str) -> None:
    async with httpx.AsyncClient(timeout=30.0) as client:
        for idx in range(subjects):
            subject_id = f"sub-{idx + 1:05d}"
            connection_id = f"{manufacturer}-conn-{subject_id}"
            payloads = generate_payloads(manufacturer, subject_id, days=days, profile=profile)
            for payload in payloads:
                headers = {
                    "x-subject-id": subject_id,
                    "x-connection-id": connection_id,
                    "x-idempotency-key": f"{run_id}-{manufacturer}-{subject_id}-{uuid4().hex[:12]}",
                    "x-device-id": f"{manufacturer}-{subject_id}",
                    "x-device-model": _device_model(manufacturer),
                    "x-device-firmware": "1.0.0",
                    "x-device-app-version": "2026.04",
                }
                try:
                    response = await client.post(f"{INGESTION_URL}/v1/ingest/{manufacturer}", headers=headers, json=payload)
                    response.raise_for_status()
                    PUSH_COUNTER.labels(manufacturer=manufacturer, status="accepted").inc()
                except Exception as exc:  # noqa: BLE001
                    PUSH_COUNTER.labels(manufacturer=manufacturer, status="failed").inc()
                    logger.exception(
                        "connector.push_failed",
                        extra={
                            "manufacturer": manufacturer,
                            "subject_id": subject_id,
                            "run_id": run_id,
                            "error": str(exc),
                            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
                        },
                    )


def _device_model(manufacturer: str) -> str:
    models = {
        "apple_healthkit": "Apple Watch Series 10",
        "android_health_connect": "Pixel Watch 3",
        "fitbit": "Fitbit Charge 6",
        "garmin": "Garmin Fenix 8",
        "oura": "Oura Ring 4",
        "whoop": "WHOOP MG",
        "withings": "Body Scan",
        "dexcom": "Dexcom G7",
    }
    return models[manufacturer]
