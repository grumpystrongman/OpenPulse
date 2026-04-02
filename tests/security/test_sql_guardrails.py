import importlib.util
from pathlib import Path

from fastapi.testclient import TestClient


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
    response = client.post("/v1/sql", json={"sql": "DELETE FROM openpulse.observation"})
    assert response.status_code == 400


def test_sql_endpoint_rejects_multi_statement(monkeypatch) -> None:
    module = _load_query_app()
    monkeypatch.setattr(module, "query", lambda _sql: [])
    client = TestClient(module.app)
    response = client.post("/v1/sql", json={"sql": "SELECT 1; SELECT 2"})
    assert response.status_code == 400
