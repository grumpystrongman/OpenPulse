from __future__ import annotations

import importlib.util
from pathlib import Path

from fastapi.testclient import TestClient


def _load_module(path: str, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, Path(path))
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


def test_consent_service_requires_role_and_token(monkeypatch) -> None:
    monkeypatch.setenv("OPENPULSE_AUTH_TOKEN", "test-token")
    module = _load_module("services/consent-identity-service/app/main.py", "consent_service_main")
    monkeypatch.setattr(module, "insert_rows", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(module, "query", lambda _sql: [])
    client = TestClient(module.app)

    missing = client.post("/v1/subjects", json={"subject_id": "sub-001"})
    assert missing.status_code == 401

    wrong_role = client.post(
        "/v1/subjects",
        json={"subject_id": "sub-001"},
        headers={"X-OpenPulse-Role": "analyst", "X-OpenPulse-Token": "test-token"},
    )
    assert wrong_role.status_code == 403

    missing_token = client.post("/v1/subjects", json={"subject_id": "sub-001"}, headers={"X-OpenPulse-Role": "admin"})
    assert missing_token.status_code == 401

    invalid_scope = client.post(
        "/v1/consents",
        json={"subject_id": "sub-001", "scope": "ingest bad"},
        headers={"X-OpenPulse-Role": "admin", "X-OpenPulse-Token": "test-token"},
    )
    assert invalid_scope.status_code == 400


def test_consent_check_requires_integration_role(monkeypatch) -> None:
    monkeypatch.setenv("OPENPULSE_AUTH_TOKEN", "test-token")
    module = _load_module("services/consent-identity-service/app/main.py", "consent_service_main_check")
    monkeypatch.setattr(module, "query", lambda _sql: [])
    client = TestClient(module.app)

    response = client.get(
        "/v1/consents/check/sub-001",
        params={"scope": "ingest:apple_healthkit"},
        headers={"X-OpenPulse-Role": "integration"},
    )
    assert response.status_code == 401


def test_ehr_service_requires_role_and_validates_literals(monkeypatch) -> None:
    monkeypatch.setenv("OPENPULSE_AUTH_TOKEN", "test-token")
    module = _load_module("services/ehr-integration/app/main.py", "ehr_service_main")
    monkeypatch.setattr(module, "query", lambda _sql: [])
    client = TestClient(module.app)

    missing = client.get("/v1/fhir/observations/sub-001", headers={"X-OpenPulse-Role": "integration"})
    assert missing.status_code == 401

    invalid_subject = client.get(
        "/v1/fhir/observations/sub 001",
        headers={"X-OpenPulse-Role": "integration", "X-OpenPulse-Token": "test-token"},
    )
    assert invalid_subject.status_code == 400

    invalid_metric = client.get(
        "/v1/export/bulk",
        params={"metric_code": "heart rate", "days": 30},
        headers={"X-OpenPulse-Role": "analyst", "X-OpenPulse-Token": "test-token"},
    )
    assert invalid_metric.status_code == 400

    invalid_days = client.get(
        "/v1/export/bulk",
        params={"days": 0},
        headers={"X-OpenPulse-Role": "analyst", "X-OpenPulse-Token": "test-token"},
    )
    assert invalid_days.status_code == 400
