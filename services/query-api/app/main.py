from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from dateutil import parser as dateparser
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import ORJSONResponse, PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from openpulse_data.clickhouse import query
from openpulse_core.security import (
    clamp_int,
    require_role,
    sanitize_select_sql,
    sql_quote,
    validate_metric_code,
    validate_subject_id,
)

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
    _auth: Any = Depends(require_role("analyst")),
) -> list[dict[str, Any]]:
    conditions = ["1=1"]
    if subject_id:
        conditions.append(f"subject_id = '{sql_quote(validate_subject_id(subject_id))}'")
    if metric_code:
        conditions.append(f"metric_code = '{sql_quote(validate_metric_code(metric_code))}'")
    limit = clamp_int(limit, minimum=1, maximum=5000, field_name="limit")
    sql = f"""
        SELECT *
        FROM openpulse.observation
        WHERE {' AND '.join(conditions)}
        ORDER BY event_time DESC
        LIMIT {limit}
    """
    return query(sql)


@app.get("/v1/timeline/{subject_id}")
def timeline(
    subject_id: str,
    from_date: str,
    to_date: str,
    _auth: Any = Depends(require_role("analyst")),
) -> list[dict[str, Any]]:
    subject_id = validate_subject_id(subject_id)
    from_ts = _parse_utc(from_date)
    to_ts = _parse_utc(to_date)
    if to_ts < from_ts:
        raise HTTPException(status_code=400, detail="to_date must be after from_date")
    sql = f"""
        SELECT subject_id, metric_code, event_time, value, unit, manufacturer, quality_score
        FROM openpulse.observation
        WHERE subject_id = '{sql_quote(subject_id)}'
          AND event_time BETWEEN toDateTime64('{from_ts.strftime("%Y-%m-%d %H:%M:%S.%f")}', 3, 'UTC')
                             AND toDateTime64('{to_ts.strftime("%Y-%m-%d %H:%M:%S.%f")}', 3, 'UTC')
        ORDER BY event_time ASC
    """
    return query(sql)


@app.get("/v1/cohorts/top-risk")
def top_risk(
    limit: int = Query(default=50, ge=1, le=1000),
    _auth: Any = Depends(require_role("analyst")),
) -> list[dict]:
    limit = clamp_int(limit, minimum=1, maximum=1000, field_name="limit")
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
def ad_hoc_sql(payload: dict[str, str], _auth: Any = Depends(require_role("operator"))) -> dict:
    sql = payload.get("sql", "").strip()
    safe_sql = sanitize_select_sql(sql, max_rows=5000)
    return {"rows": query(safe_sql)}


def _parse_utc(value: str) -> datetime:
    try:
        parsed = dateparser.isoparse(value).astimezone(timezone.utc)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Invalid datetime: {value}") from exc
    return parsed
