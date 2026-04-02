from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import ORJSONResponse, PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from openpulse_data.clickhouse import query

app = FastAPI(
    title="OpenPulse Query API",
    version="0.1.0",
    default_response_class=ORJSONResponse,
    description="Operator and analytics query API over OpenPulse warehouse tables.",
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "query-api", "timestamp": datetime.now(tz=timezone.utc).isoformat()}


@app.get("/metrics")
def metrics() -> PlainTextResponse:
    return PlainTextResponse(generate_latest().decode("utf-8"), media_type=CONTENT_TYPE_LATEST)


@app.get("/v1/observations")
def observations(
    subject_id: str | None = Query(default=None),
    metric_code: str | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=5000),
) -> list[dict[str, Any]]:
    conditions = ["1=1"]
    if subject_id:
        conditions.append(f"subject_id = '{subject_id}'")
    if metric_code:
        conditions.append(f"metric_code = '{metric_code}'")
    sql = f"""
        SELECT *
        FROM openpulse.observation
        WHERE {' AND '.join(conditions)}
        ORDER BY event_time DESC
        LIMIT {limit}
    """
    return query(sql)


@app.get("/v1/timeline/{subject_id}")
def timeline(subject_id: str, from_date: str, to_date: str) -> list[dict[str, Any]]:
    sql = f"""
        SELECT subject_id, metric_code, event_time, value, unit, manufacturer, quality_score
        FROM openpulse.observation
        WHERE subject_id = '{subject_id}'
          AND event_time BETWEEN toDateTime64('{from_date}', 3, 'UTC')
                             AND toDateTime64('{to_date}', 3, 'UTC')
        ORDER BY event_time ASC
    """
    return query(sql)


@app.get("/v1/cohorts/top-risk")
def top_risk(limit: int = Query(default=50, ge=1, le=1000)) -> list[dict]:
    sql = f"""
        SELECT
          subject_id,
          avgIf(value, metric_code = 'glucose') AS avg_glucose,
          avgIf(value, metric_code = 'recovery_score') AS avg_recovery,
          avgIf(value, metric_code = 'stress_score') AS avg_stress,
          count() AS points
        FROM openpulse.observation
        GROUP BY subject_id
        ORDER BY avg_glucose DESC NULLS LAST, avg_stress DESC NULLS LAST, avg_recovery ASC NULLS LAST
        LIMIT {limit}
    """
    return query(sql)


@app.post("/v1/sql")
def ad_hoc_sql(payload: dict[str, str]) -> dict:
    sql = payload.get("sql", "").strip()
    if not sql.lower().startswith("select"):
        raise HTTPException(status_code=400, detail="Only SELECT statements are allowed")
    if ";" in sql.rstrip(";"):
        raise HTTPException(status_code=400, detail="Multiple statements are not allowed")
    return {"rows": query(sql)}
