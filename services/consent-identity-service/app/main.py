from __future__ import annotations

import hashlib
import os
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import ORJSONResponse, PlainTextResponse
from pydantic import BaseModel, Field
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from openpulse_data.clickhouse import insert_rows, query
from openpulse_core.security import (
    require_role,
    sql_quote,
    validate_consent_id,
    validate_scope,
    validate_subject_id,
)

app = FastAPI(
    title="OpenPulse Consent Identity Service",
    version="0.1.0",
    default_response_class=ORJSONResponse,
    description="Subject identity linkage, pseudonymization, and consent enforcement service.",
)

SALT = os.getenv("PSEUDONYMIZATION_SALT", "openpulse-dev-salt")


class SubjectCreate(BaseModel):
    subject_id: str
    attributes: dict = Field(default_factory=dict)


class ConsentCreate(BaseModel):
    subject_id: str
    scope: str
    expires_at: datetime | None = None


SubjectCreate.model_rebuild()
ConsentCreate.model_rebuild()


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "consent-identity-service"}


@app.get("/metrics")
def metrics() -> PlainTextResponse:
    return PlainTextResponse(generate_latest().decode("utf-8"), media_type=CONTENT_TYPE_LATEST)


@app.post("/v1/subjects")
def create_subject(payload: SubjectCreate, _auth: object = Depends(require_role("admin"))) -> dict:
    subject_id = validate_subject_id(payload.subject_id)
    pseudonym = hashlib.sha256(f"{SALT}:{subject_id}".encode("utf-8")).hexdigest()
    insert_rows(
        "subject",
        [
            {
                "subject_id": subject_id,
                "pseudonym_id": pseudonym,
                "created_at": datetime.now(tz=timezone.utc),
                "attributes_json": str(payload.attributes),
            }
        ],
    )
    return {"subject_id": subject_id, "pseudonym_id": pseudonym}


@app.post("/v1/consents")
def create_consent(payload: ConsentCreate, _auth: object = Depends(require_role("admin"))) -> dict:
    subject_id = validate_subject_id(payload.subject_id)
    scope = validate_scope(payload.scope)
    consent_id = uuid4().hex
    insert_rows(
        "consent",
        [
            {
                "consent_id": consent_id,
                "subject_id": subject_id,
                "scope": scope,
                "status": "granted",
                "granted_at": datetime.now(tz=timezone.utc),
                "revoked_at": None,
                "expires_at": payload.expires_at,
                "source": "api",
                "policy_version": "1.0.0",
            }
        ],
    )
    return {"consent_id": consent_id, "status": "granted"}


@app.post("/v1/consents/{consent_id}/revoke")
def revoke_consent(consent_id: str, _auth: object = Depends(require_role("admin"))) -> dict:
    consent_id = validate_consent_id(consent_id)
    rows = query(
        f"SELECT consent_id, subject_id, scope FROM openpulse.consent WHERE consent_id = '{sql_quote(consent_id)}' LIMIT 1"
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Consent not found")
    record = rows[0]
    insert_rows(
        "consent",
        [
            {
                "consent_id": record["consent_id"],
                "subject_id": record["subject_id"],
                "scope": record["scope"],
                "status": "revoked",
                "granted_at": datetime.now(tz=timezone.utc),
                "revoked_at": datetime.now(tz=timezone.utc),
                "expires_at": None,
                "source": "api",
                "policy_version": "1.0.0",
            }
        ],
    )
    return {"consent_id": consent_id, "status": "revoked"}


@app.get("/v1/consents/check/{subject_id}")
def check_consent(subject_id: str, scope: str, _auth: object = Depends(require_role("integration"))) -> dict:
    subject_id = validate_subject_id(subject_id)
    scope = validate_scope(scope)
    sql = f"""
        SELECT status, expires_at, max(granted_at) AS granted_at
        FROM openpulse.consent
        WHERE subject_id = '{sql_quote(subject_id)}' AND scope = '{sql_quote(scope)}'
        GROUP BY status, expires_at
        ORDER BY granted_at DESC
        LIMIT 1
    """
    rows = query(sql)
    if not rows:
        return {"allowed": False, "reason": "no_consent"}
    status = rows[0]["status"]
    if status != "granted":
        return {"allowed": False, "reason": status}
    expires_at = rows[0].get("expires_at")
    if expires_at and expires_at < datetime.now(tz=timezone.utc):
        return {"allowed": False, "reason": "expired"}
    return {"allowed": True, "reason": "granted"}
