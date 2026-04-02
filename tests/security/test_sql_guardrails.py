import importlib.util
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

HEADERS = {"X-OpenPulse-Role": "operator"}


@pytest.fixture(autouse=True)
def _clear_auth_token(monkeypatch) -> None:
    monkeypatch.delenv("OPENPULSE_AUTH_TOKEN", raising=False)


def _load_query_app():
    path = Path("services/query-api/app/main.py")
    spec = importlib.util.spec_from_file_location("query_api_main", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


def test_sql_endpoint_blocks_non_select(monkeypatch) -> None:
    module = _load_query_app()
    monkeypatch.setattr(module, "query", lambda _sql: [])
    client = TestClient(module.app)
    response = client.post("/v1/sql", json={"sql": "DELETE FROM openpulse.observation"}, headers=HEADERS)
    assert response.status_code == 400


def test_sql_endpoint_rejects_multi_statement(monkeypatch) -> None:
    module = _load_query_app()
    monkeypatch.setattr(module, "query", lambda _sql: [])
    client = TestClient(module.app)
    response = client.post("/v1/sql", json={"sql": "SELECT 1; SELECT 2"}, headers=HEADERS)
    assert response.status_code == 400


def test_sql_endpoint_requires_operator_role() -> None:
    module = _load_query_app()
    client = TestClient(module.app)
    response = client.post("/v1/sql", json={"sql": "SELECT 1"}, headers={"X-OpenPulse-Role": "analyst"})
    assert response.status_code == 403


def test_sql_endpoint_appends_limit_and_blocks_keywords(monkeypatch) -> None:
    module = _load_query_app()
    captured = {"sql": ""}

    def _fake_query(sql: str):
        captured["sql"] = sql
        return []

    monkeypatch.setattr(module, "query", _fake_query)
    client = TestClient(module.app)

    ok = client.post("/v1/sql", json={"sql": "SELECT subject_id FROM openpulse.observation"}, headers=HEADERS)
    assert ok.status_code == 200
    assert "LIMIT 5000" in captured["sql"]

    capped = client.post("/v1/sql", json={"sql": "SELECT subject_id FROM openpulse.observation LIMIT 9001"}, headers=HEADERS)
    assert capped.status_code == 200
    assert "LIMIT 5000" in captured["sql"]

    blocked = client.post(
        "/v1/sql",
        json={"sql": "SELECT * FROM openpulse.observation DROP TABLE openpulse.observation"},
        headers=HEADERS,
    )
    assert blocked.status_code == 400
