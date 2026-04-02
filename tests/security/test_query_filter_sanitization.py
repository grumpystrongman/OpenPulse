import importlib.util
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

HEADERS = {"X-OpenPulse-Role": "analyst"}


@pytest.fixture(autouse=True)
def _clear_auth_token(monkeypatch) -> None:
    monkeypatch.delenv("OPENPULSE_AUTH_TOKEN", raising=False)


def _load_query_app():
    path = Path("services/query-api/app/main.py")
    spec = importlib.util.spec_from_file_location("query_api_main_for_sanitize", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


def test_observations_escapes_filters(monkeypatch) -> None:
    module = _load_query_app()
    captured = {"sql": ""}

    def _fake_query(sql: str):
        captured["sql"] = sql
        return []

    monkeypatch.setattr(module, "query", _fake_query)
    client = TestClient(module.app)
    response = client.get("/v1/observations", params={"subject_id": "sub-001", "metric_code": "heart_rate"}, headers=HEADERS)
    assert response.status_code == 200
    assert "subject_id = 'sub-001'" in captured["sql"]
    assert "metric_code = 'heart_rate'" in captured["sql"]


def test_observations_rejects_injection_like_subject_id(monkeypatch) -> None:
    module = _load_query_app()
    monkeypatch.setattr(module, "query", lambda _sql: [])
    client = TestClient(module.app)
    response = client.get(
        "/v1/observations",
        params={"subject_id": "a' OR 1=1 --", "metric_code": "heart_rate"},
        headers=HEADERS,
    )
    assert response.status_code == 400


def test_observations_rejects_invalid_metric_code(monkeypatch) -> None:
    module = _load_query_app()
    monkeypatch.setattr(module, "query", lambda _sql: [])
    client = TestClient(module.app)
    response = client.get("/v1/observations", params={"subject_id": "sub-001", "metric_code": "heart rate"}, headers=HEADERS)
    assert response.status_code == 400


def test_timeline_rejects_invalid_datetime(monkeypatch) -> None:
    module = _load_query_app()
    monkeypatch.setattr(module, "query", lambda _sql: [])
    client = TestClient(module.app)
    response = client.get(
        "/v1/timeline/sub-1",
        params={"from_date": "bad", "to_date": "2026-01-01T00:00:00Z"},
        headers=HEADERS,
    )
    assert response.status_code == 400


def test_timeline_rejects_invalid_subject_id(monkeypatch) -> None:
    module = _load_query_app()
    monkeypatch.setattr(module, "query", lambda _sql: [])
    client = TestClient(module.app)
    response = client.get(
        "/v1/timeline/sub 1",
        params={"from_date": "2026-01-01T00:00:00Z", "to_date": "2026-01-02T00:00:00Z"},
        headers=HEADERS,
    )
    assert response.status_code == 400
