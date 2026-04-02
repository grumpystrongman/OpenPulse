from __future__ import annotations

import logging
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, ORJSONResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import BaseModel, Field

app = FastAPI(
    title="OpenPulse Ops Console",
    version="0.1.0",
    default_response_class=ORJSONResponse,
    description="Operations console for connector status, data quality, and governance visibility.",
)

logger = logging.getLogger("openpulse.ops_console")
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
QUERY_API_URL = os.getenv("QUERY_API_URL", "http://query-api:8003")
CONNECTOR_API_URL = os.getenv("CONNECTOR_API_URL", "http://connector-service:8002")
GOVERNOR_API_URL = os.getenv("GOVERNOR_API_URL", "http://governance-agent:8005")
INTERNAL_ROLE = os.getenv("OPENPULSE_INTERNAL_ROLE", "operator")
AUTH_TOKEN = os.getenv("OPENPULSE_AUTH_TOKEN", "")
SERVICES: dict[str, str] = {
    "ingestion_gateway": "http://ingestion-gateway:8001/health",
    "connector_service": "http://connector-service:8002/health",
    "query_api": "http://query-api:8003/health",
    "consent_identity_service": "http://consent-identity-service:8004/health",
    "governance_agent": "http://governance-agent:8005/health",
    "ehr_integration": "http://ehr-integration:8006/health",
    "ops_console": "http://ops-console:8007/health",
}


class DemoRunRequest(BaseModel):
    subjects: int = Field(default=2, ge=1, le=100)
    days: int = Field(default=7, ge=1, le=365)
    profile: str = Field(default="healthy", pattern="^(healthy|athletic|at_risk|chronic)$")


class GovernanceReviewRequest(BaseModel):
    proposal_id: str = Field(min_length=3, max_length=120)
    proposal_type: str = Field(pattern="^(schema_change|roadmap_change|breaking_change|connector_priority|release)$")
    summary: str = Field(min_length=10, max_length=1000)
    impact_scope: str = Field(pattern="^(low|medium|high)$")
    adoption_benefit: int = Field(ge=1, le=10, default=7)
    implementation_cost: int = Field(ge=1, le=10, default=5)
    community_impact: int = Field(ge=1, le=10, default=7)
    security_risk: int = Field(ge=1, le=10, default=4)
    backward_compatible: bool = True


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "ops-console", "timestamp": datetime.now(tz=timezone.utc).isoformat()}


@app.get("/metrics")
def metrics() -> PlainTextResponse:
    return PlainTextResponse(generate_latest().decode("utf-8"), media_type=CONTENT_TYPE_LATEST)


@app.get("/")
async def dashboard(request: Request) -> Any:
    async with httpx.AsyncClient(timeout=10.0) as client:
        top_risk = await _safe_get(client, f"{QUERY_API_URL}/v1/cohorts/top-risk?limit=10", role="analyst")
        decisions = await _safe_get(client, f"{GOVERNOR_API_URL}/v1/decisions")
        summary = await _summary_or_default(client)

    context = {
        "request": request,
        "summary": summary,
        "top_risk": top_risk if isinstance(top_risk, list) else [],
        "decisions": decisions if isinstance(decisions, list) else [],
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
    }
    try:
        return templates.TemplateResponse("index.html", context)
    except Exception as exc:  # noqa: BLE001
        logger.exception("ops_console.template_render_failed", extra={"error": str(exc)})
        return HTMLResponse(_render_fallback_dashboard(context), status_code=200)


@app.get("/api/health-summary")
async def health_summary() -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=5.0) as client:
        checks: dict[str, dict[str, Any] | list[Any]] = {}
        for name, url in SERVICES.items():
            checks[name] = await _safe_get(client, url)
        up = sum(1 for value in checks.values() if isinstance(value, dict) and value.get("status") == "ok")
        total = len(checks)
        return {
            "status": "ok" if up == total else "degraded",
            "checks": checks,
            "up": up,
            "total": total,
            "generated_at": _now_iso(),
        }


@app.get("/api/summary")
async def summary() -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=20.0) as client:
        return await _summary_or_default(client)


@app.get("/api/cohort-top-risk")
async def cohort_top_risk(limit: int = Query(default=10, ge=1, le=200)) -> list[dict[str, Any]]:
    async with httpx.AsyncClient(timeout=15.0) as client:
        rows = await _safe_get(client, f"{QUERY_API_URL}/v1/cohorts/top-risk?limit={limit}", role="analyst")
        return rows if isinstance(rows, list) else []


@app.get("/api/governance-decisions")
async def governance_decisions() -> list[dict[str, Any]]:
    async with httpx.AsyncClient(timeout=10.0) as client:
        rows = await _safe_get(client, f"{GOVERNOR_API_URL}/v1/decisions")
        return rows if isinstance(rows, list) else []


@app.post("/api/run-simulation")
async def run_simulation(payload: DemoRunRequest) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{CONNECTOR_API_URL}/v1/simulate-all",
                params={"subjects": payload.subjects, "days": payload.days, "profile": payload.profile},
                headers=_service_headers("operator"),
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=exc.response.status_code, detail=_downstream_detail(exc.response)) from exc
        except (httpx.RequestError, ValueError) as exc:
            raise HTTPException(status_code=502, detail="Connector service unavailable") from exc


@app.post("/api/governance-review")
async def governance_review(payload: GovernanceReviewRequest) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.post(
                f"{GOVERNOR_API_URL}/v1/review",
                json=payload.model_dump(),
                headers=_service_headers("operator"),
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=exc.response.status_code, detail=_downstream_detail(exc.response)) from exc
        except (httpx.RequestError, ValueError) as exc:
            raise HTTPException(status_code=502, detail="Governance service unavailable") from exc


async def _safe_get(client: httpx.AsyncClient, url: str, role: str | None = None) -> dict[str, Any] | list[Any]:
    try:
        response = await client.get(url, headers=_service_headers(role))
        response.raise_for_status()
        return response.json()
    except Exception:  # noqa: BLE001
        return {"status": "down", "url": url}


async def _safe_sql(client: httpx.AsyncClient, sql: str) -> list[dict[str, Any]]:
    try:
        response = await client.post(
            f"{QUERY_API_URL}/v1/sql",
            json={"sql": sql},
            headers=_service_headers("operator"),
        )
        response.raise_for_status()
        payload = response.json()
        rows = payload.get("rows", [])
        return rows if isinstance(rows, list) else []
    except Exception:  # noqa: BLE001
        return []


async def _compute_summary(client: httpx.AsyncClient) -> dict[str, Any]:
    total_observations = await _safe_sql(client, "SELECT count() AS c FROM openpulse.observation")
    subjects = await _safe_sql(client, "SELECT uniq(subject_id) AS c FROM openpulse.observation")
    manufacturers = await _safe_sql(
        client,
        "SELECT manufacturer, count() AS c FROM openpulse.observation GROUP BY manufacturer ORDER BY c DESC",
    )
    metric_mix = await _safe_sql(
        client,
        "SELECT metric_code, count() AS c FROM openpulse.observation GROUP BY metric_code ORDER BY c DESC LIMIT 12",
    )
    recent = await _safe_sql(
        client,
        "SELECT subject_id, manufacturer, metric_code, value, unit, event_time FROM openpulse.observation ORDER BY event_time DESC LIMIT 25",
    )
    avg_quality = await _safe_sql(client, "SELECT round(avg(score), 4) AS avg_score FROM openpulse.quality_assessment")
    failed_queue = await _safe_sql(
        client,
        "SELECT replay_status, count() AS c FROM openpulse.failed_record_queue GROUP BY replay_status ORDER BY c DESC",
    )
    run_status = await _safe_sql(
        client,
        "SELECT status, count() AS c FROM openpulse.normalization_run GROUP BY status ORDER BY c DESC",
    )

    return {
        "status": "ok",
        "generated_at": _now_iso(),
        "total_observations": int(total_observations[0]["c"]) if total_observations else 0,
        "subjects": int(subjects[0]["c"]) if subjects else 0,
        "avg_quality": float(avg_quality[0]["avg_score"]) if avg_quality and avg_quality[0]["avg_score"] is not None else None,
        "manufacturers": manufacturers,
        "metric_mix": metric_mix,
        "recent_observations": recent,
        "failed_queue": failed_queue,
        "normalization_runs": run_status,
    }


async def _summary_or_default(client: httpx.AsyncClient) -> dict[str, Any]:
    try:
        return await _compute_summary(client)
    except Exception as exc:  # noqa: BLE001
        logger.exception("ops_console.summary_failed", extra={"error": str(exc)})
        return _empty_summary(status="degraded", errors=[str(exc)])


def _empty_summary(status: str = "ok", errors: list[str] | None = None) -> dict[str, Any]:
    return {
        "status": status,
        "errors": errors or [],
        "generated_at": _now_iso(),
        "total_observations": 0,
        "subjects": 0,
        "avg_quality": None,
        "manufacturers": [],
        "metric_mix": [],
        "recent_observations": [],
        "failed_queue": [],
        "normalization_runs": [],
    }


def _downstream_detail(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except Exception:  # noqa: BLE001
        payload = response.text
    if isinstance(payload, dict):
        detail = payload.get("detail") or payload.get("message") or payload
        return str(detail)
    return str(payload)


def _service_headers(role: str | None = None) -> dict[str, str]:
    headers = {"X-OpenPulse-Role": role or INTERNAL_ROLE}
    if AUTH_TOKEN:
        headers["X-OpenPulse-Token"] = AUTH_TOKEN
    return headers


def _render_fallback_dashboard(context: dict[str, Any]) -> str:
    summary = context.get("summary") or _empty_summary(status="degraded", errors=["template render failure"])
    errors = summary.get("errors") or []
    status = summary.get("status") or "degraded"
    top_risk = context.get("top_risk") or []
    decisions = context.get("decisions") or []
    return f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>OpenPulse Demo Console</title>
    <style>
      body {{ font-family: Arial, sans-serif; margin: 0; padding: 2rem; background: #f1f5f9; color: #0f172a; }}
      .card {{ background: #fff; border: 1px solid #dbe5ef; border-radius: 12px; padding: 1rem; margin-bottom: 1rem; }}
      .pill {{ display: inline-block; padding: 0.2rem 0.5rem; border-radius: 999px; background: #d1fae5; color: #065f46; }}
      .pill.degraded {{ background: #fee2e2; color: #991b1b; }}
      ul {{ margin: 0.5rem 0 0; }}
    </style>
  </head>
  <body>
    <div class="card">
      <h1>OpenPulse Demo Console</h1>
      <div class="pill {'degraded' if status != 'ok' else ''}">{status}</div>
      <p>Fallback rendering was used because the full template path failed.</p>
      <p>Rendered at {context.get('timestamp')}</p>
      <p>Observations: {summary.get('total_observations', 0)} | Subjects: {summary.get('subjects', 0)}</p>
      {"<p>Errors: " + ", ".join(errors) + "</p>" if errors else ""}
    </div>
    <div class="card">
      <h2>Top Risk Cohort</h2>
      <p>{len(top_risk)} rows available.</p>
    </div>
    <div class="card">
      <h2>Recent Governance Decisions</h2>
      <p>{len(decisions)} decisions available.</p>
    </div>
  </body>
</html>"""


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()
