from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
from typing import Literal
from uuid import uuid4

import yaml
from fastapi import FastAPI, HTTPException
from fastapi.responses import ORJSONResponse, PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import BaseModel, Field

app = FastAPI(
    title="openpulse-governor-jeff",
    version="0.1.0",
    default_response_class=ORJSONResponse,
    description="Rules-driven governance and release gate decision service for OpenPulse.",
)


class ReviewRequest(BaseModel):
    proposal_id: str
    proposal_type: Literal["schema_change", "roadmap_change", "breaking_change", "connector_priority", "release"]
    summary: str
    impact_scope: Literal["low", "medium", "high"]
    adoption_benefit: int = Field(ge=1, le=10)
    implementation_cost: int = Field(ge=1, le=10)
    community_impact: int = Field(ge=1, le=10)
    security_risk: int = Field(ge=1, le=10)
    backward_compatible: bool = True


class OverrideRequest(BaseModel):
    proposal_id: str
    decision: Literal["approve", "approve_with_conditions", "reject"]
    rationale: str
    actor: str


DECISIONS: dict[str, dict] = {}


def _load_policy() -> dict:
    policy_path = Path(os.getenv("GOVERNOR_POLICY_PATH", Path(__file__).parent / "policy" / "default_policy.yaml"))
    with policy_path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


POLICY = _load_policy()


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "openpulse-governor-jeff", "policy_version": POLICY["version"]}


@app.get("/metrics")
def metrics() -> PlainTextResponse:
    return PlainTextResponse(generate_latest().decode("utf-8"), media_type=CONTENT_TYPE_LATEST)


@app.post("/v1/review")
def review(payload: ReviewRequest) -> dict:
    risk_score = _calculate_risk(payload)
    decision = _decision(payload, risk_score)
    conditions = _conditions(payload, risk_score)
    artifact = {
        "decision_id": uuid4().hex,
        "proposal_id": payload.proposal_id,
        "decision": decision,
        "rationale": _rationale(payload, risk_score, decision),
        "risk_score": risk_score,
        "adoption_impact": payload.adoption_benefit,
        "implementation_cost_estimate": payload.implementation_cost,
        "community_impact": payload.community_impact,
        "conditions": conditions,
        "policy_version": POLICY["version"],
        "created_at": datetime.now(tz=timezone.utc).isoformat(),
        "override": None,
    }
    DECISIONS[payload.proposal_id] = artifact
    return artifact


@app.post("/v1/override")
def override(payload: OverrideRequest) -> dict:
    if payload.proposal_id not in DECISIONS:
        raise HTTPException(status_code=404, detail="Proposal decision not found")
    DECISIONS[payload.proposal_id]["override"] = {
        "decision": payload.decision,
        "rationale": payload.rationale,
        "actor": payload.actor,
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
    }
    DECISIONS[payload.proposal_id]["decision"] = payload.decision
    DECISIONS[payload.proposal_id]["rationale"] = payload.rationale
    return DECISIONS[payload.proposal_id]


@app.get("/v1/decisions")
def list_decisions() -> list[dict]:
    return list(DECISIONS.values())


def _calculate_risk(payload: ReviewRequest) -> float:
    policy_weights = POLICY["weights"]
    score = (
        payload.security_risk * policy_weights["security_risk"]
        + payload.implementation_cost * policy_weights["implementation_cost"]
        + (10 - payload.adoption_benefit) * policy_weights["adoption_penalty"]
        + (10 - payload.community_impact) * policy_weights["community_penalty"]
    )
    if not payload.backward_compatible:
        score += POLICY["non_backward_compatible_penalty"]
    if payload.impact_scope == "high":
        score += POLICY["high_scope_penalty"]
    elif payload.impact_scope == "medium":
        score += POLICY["medium_scope_penalty"]
    return round(min(100.0, max(0.0, score * 3.5)), 2)


def _decision(payload: ReviewRequest, risk_score: float) -> str:
    thresholds = POLICY["decision_thresholds"]
    if payload.proposal_type == "breaking_change" and not payload.backward_compatible and risk_score >= thresholds["reject"]:
        return "reject"
    if risk_score >= thresholds["reject"]:
        return "reject"
    if risk_score >= thresholds["conditional"]:
        return "approve_with_conditions"
    return "approve"


def _conditions(payload: ReviewRequest, risk_score: float) -> list[str]:
    conditions: list[str] = []
    if risk_score >= POLICY["decision_thresholds"]["conditional"]:
        conditions.append("Require staged rollout and rollback plan.")
    if not payload.backward_compatible:
        conditions.append("Publish migration guide and compatibility matrix before merge.")
    if payload.security_risk >= 7:
        conditions.append("Security review sign-off required.")
    if payload.proposal_type == "schema_change":
        conditions.append("Update conformance kit and versioned schemas.")
    return conditions


def _rationale(payload: ReviewRequest, risk_score: float, decision: str) -> str:
    return (
        f"Decision={decision}. Risk score {risk_score}. "
        f"Adoption benefit {payload.adoption_benefit}/10, implementation cost {payload.implementation_cost}/10, "
        f"community impact {payload.community_impact}/10, backward_compatible={payload.backward_compatible}."
    )
