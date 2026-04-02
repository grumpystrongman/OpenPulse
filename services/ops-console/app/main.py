from __future__ import annotations

from datetime import datetime, timezone

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import ORJSONResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

app = FastAPI(
    title="OpenPulse Ops Console",
    version="0.1.0",
    default_response_class=ORJSONResponse,
    description="Operations console for connector status, data quality, and governance visibility.",
)

templates = Jinja2Templates(directory="app/templates")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "ops-console", "timestamp": datetime.now(tz=timezone.utc).isoformat()}


@app.get("/metrics")
def metrics() -> PlainTextResponse:
    return PlainTextResponse(generate_latest().decode("utf-8"), media_type=CONTENT_TYPE_LATEST)


@app.get("/")
async def dashboard(request: Request):
    async with httpx.AsyncClient(timeout=5.0) as client:
        query_health = await _safe_get(client, "http://query-api:8003/health")
        governor_health = await _safe_get(client, "http://governance-agent:8005/health")
        top_risk = await _safe_get(client, "http://query-api:8003/v1/cohorts/top-risk?limit=10")
        decisions = await _safe_get(client, "http://governance-agent:8005/v1/decisions")
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "query_health": query_health,
            "governor_health": governor_health,
            "top_risk": top_risk if isinstance(top_risk, list) else [],
            "decisions": decisions if isinstance(decisions, list) else [],
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        },
    )


async def _safe_get(client: httpx.AsyncClient, url: str):
    try:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()
    except Exception:  # noqa: BLE001
        return {"status": "down", "url": url}
