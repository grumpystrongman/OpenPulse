from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from threading import Lock
from typing import Any
from uuid import uuid4

import httpx
from fastapi import BackgroundTasks, FastAPI, HTTPException, Query
from fastapi.responses import ORJSONResponse, PlainTextResponse
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
CONSENT_IDENTITY_URL = os.getenv("OPENPULSE_CONSENT_BASE_URL", "http://consent-identity-service:8004").rstrip("/")
AUTH_TOKEN = os.getenv("OPENPULSE_AUTH_TOKEN", "")

RUN_STATE_LOCK = Lock()
SIMULATION_RUNS: dict[str, dict[str, Any]] = {}


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


@app.get("/v1/runs")
def list_runs(limit: int = Query(default=25, ge=1, le=200)) -> list[dict[str, Any]]:
    with RUN_STATE_LOCK:
        items = list(SIMULATION_RUNS.values())
    items.sort(key=lambda x: x["created_at"], reverse=True)
    return items[:limit]


@app.get("/v1/runs/{run_id}")
def get_run(run_id: str) -> dict[str, Any]:
    with RUN_STATE_LOCK:
        run = SIMULATION_RUNS.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


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
    _create_run(run_id, [manufacturer], subjects, days, profile)
    background_tasks.add_task(_run_simulation, manufacturer, subjects, days, profile, run_id)
    return {"status": "started", "run_id": run_id, "manufacturer": manufacturer}


@app.post("/v1/simulate-all")
async def simulate_all(
    background_tasks: BackgroundTasks,
    subjects: int = Query(default=2, ge=1, le=500),
    days: int = Query(default=2, ge=1, le=365),
    profile: str = Query(default="healthy", pattern="^(healthy|athletic|at_risk|chronic)$"),
) -> dict:
    run_id = uuid4().hex
    manufacturers = list(CAPABILITY_REGISTRY.keys())
    _create_run(run_id, manufacturers, subjects, days, profile)
    for manufacturer in manufacturers:
        background_tasks.add_task(_run_simulation, manufacturer, subjects, days, profile, run_id)
    return {"status": "started", "run_id": run_id, "manufacturers": manufacturers}


async def _run_simulation(manufacturer: str, subjects: int, days: int, profile: str, run_id: str) -> None:
    _set_manufacturer_status(run_id, manufacturer, "running")
    accepted = 0
    failed = 0
    last_error: str | None = None

    async with httpx.AsyncClient(timeout=30.0) as client:
        for idx in range(subjects):
            subject_id = f"sub-{idx + 1:05d}"
            connection_id = f"{manufacturer}-conn-{subject_id}"
            await _ensure_subject_and_consent(client, subject_id, manufacturer)
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
                    accepted += 1
                except Exception as exc:  # noqa: BLE001
                    PUSH_COUNTER.labels(manufacturer=manufacturer, status="failed").inc()
                    failed += 1
                    last_error = str(exc)
                    logger.exception(
                        "connector.push_failed",
                        extra={
                            "manufacturer": manufacturer,
                            "subject_id": subject_id,
                            "run_id": run_id,
                            "error": last_error,
                            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
                        },
                    )

    _complete_manufacturer(run_id, manufacturer, accepted, failed, last_error)


async def _ensure_subject_and_consent(client: httpx.AsyncClient, subject_id: str, manufacturer: str) -> None:
    headers = {"X-OpenPulse-Role": "admin"}
    if AUTH_TOKEN:
        headers["X-OpenPulse-Token"] = AUTH_TOKEN

    subject_payload = {"subject_id": subject_id, "attributes": {"source": "connector-service"}}
    consent_payload = {"subject_id": subject_id, "scope": f"ingest:{manufacturer}"}

    try:
        subject_response = await client.post(f"{CONSENT_IDENTITY_URL}/v1/subjects", json=subject_payload, headers=headers)
        subject_response.raise_for_status()
        consent_response = await client.post(
            f"{CONSENT_IDENTITY_URL}/v1/consents",
            json=consent_payload,
            headers=headers,
        )
        consent_response.raise_for_status()
    except Exception:  # noqa: BLE001
        logger.exception(
            "connector.consent_seed_failed",
            extra={
                "subject_id": subject_id,
                "manufacturer": manufacturer,
                "consent_identity_url": CONSENT_IDENTITY_URL,
            },
        )
        raise


def _create_run(run_id: str, manufacturers: list[str], subjects: int, days: int, profile: str) -> None:
    now = datetime.now(tz=timezone.utc).isoformat()
    with RUN_STATE_LOCK:
        SIMULATION_RUNS[run_id] = {
            "run_id": run_id,
            "status": "running",
            "created_at": now,
            "updated_at": now,
            "subjects": subjects,
            "days": days,
            "profile": profile,
            "manufacturers": {
                m: {
                    "status": "pending",
                    "accepted": 0,
                    "failed": 0,
                    "last_error": None,
                    "completed_at": None,
                }
                for m in manufacturers
            },
        }


def _set_manufacturer_status(run_id: str, manufacturer: str, status: str) -> None:
    with RUN_STATE_LOCK:
        if run_id not in SIMULATION_RUNS or manufacturer not in SIMULATION_RUNS[run_id]["manufacturers"]:
            return
        SIMULATION_RUNS[run_id]["manufacturers"][manufacturer]["status"] = status
        SIMULATION_RUNS[run_id]["updated_at"] = datetime.now(tz=timezone.utc).isoformat()


def _complete_manufacturer(run_id: str, manufacturer: str, accepted: int, failed: int, last_error: str | None) -> None:
    with RUN_STATE_LOCK:
        run = SIMULATION_RUNS.get(run_id)
        if not run:
            return
        state = run["manufacturers"].get(manufacturer)
        if not state:
            return
        state["status"] = "completed_with_errors" if failed > 0 else "completed"
        state["accepted"] = accepted
        state["failed"] = failed
        state["last_error"] = last_error
        state["completed_at"] = datetime.now(tz=timezone.utc).isoformat()
        run["updated_at"] = datetime.now(tz=timezone.utc).isoformat()

        statuses = [m["status"] for m in run["manufacturers"].values()]
        if all(s in {"completed", "completed_with_errors"} for s in statuses):
            run["status"] = "completed_with_errors" if any(s == "completed_with_errors" for s in statuses) else "completed"


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
