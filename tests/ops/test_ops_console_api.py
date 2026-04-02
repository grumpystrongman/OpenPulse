import importlib.util
from pathlib import Path

import httpx
from fastapi.testclient import TestClient


def _load_ops_console():
    path = Path("services/ops-console/app/main.py")
    spec = importlib.util.spec_from_file_location("ops_console_main", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


class _DummyResponse:
    def __init__(self, status_code: int, payload: dict | list | None = None, text: str = "upstream error") -> None:
        self.status_code = status_code
        self._payload = payload if payload is not None else {"detail": text}
        self.text = text
        self.request = httpx.Request("POST", "http://example.test")

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("upstream error", request=self.request, response=self)

    def json(self):
        return self._payload


class _DummyAsyncClient:
    def __init__(self, *, get_payload=None, post_response=None, post_error=None) -> None:
        self.get_payload = get_payload
        self.post_response = post_response
        self.post_error = post_error

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url: str):
        if callable(self.get_payload):
            return self.get_payload(url)
        if self.get_payload is not None:
            return self.get_payload
        return _DummyResponse(200, {"status": "ok", "url": url})

    async def post(self, *args, **kwargs):
        if self.post_error is not None:
            raise self.post_error
        if self.post_response is not None:
            return self.post_response
        return _DummyResponse(200, {"status": "started", "run_id": "demo"})


def test_dashboard_returns_200_when_template_render_fails(monkeypatch) -> None:
    module = _load_ops_console()
    client = TestClient(module.app)

    async def _summary(_client):
        return {
            "status": "ok",
            "generated_at": "2026-04-02T00:00:00Z",
            "total_observations": 12,
            "subjects": 3,
            "avg_quality": 0.98,
            "manufacturers": [],
            "metric_mix": [],
            "recent_observations": [],
            "failed_queue": [],
            "normalization_runs": [],
        }

    async def _safe_get(_client, _url, role=None):  # noqa: ARG001
        return []

    def _boom(*args, **kwargs):
        raise RuntimeError("template unavailable")

    monkeypatch.setattr(module, "_summary_or_default", _summary)
    monkeypatch.setattr(module, "_safe_get", _safe_get)
    monkeypatch.setattr(module.templates, "TemplateResponse", _boom)

    response = client.get("/")
    assert response.status_code == 200
    assert "Fallback rendering was used" in response.text


def test_summary_degrades_when_backend_summary_fails(monkeypatch) -> None:
    module = _load_ops_console()
    client = TestClient(module.app)

    async def _boom(_client):
        raise RuntimeError("query api down")

    monkeypatch.setattr(module, "_compute_summary", _boom)

    response = client.get("/api/summary")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "degraded"
    assert body["total_observations"] == 0
    assert body["manufacturers"] == []


def test_health_summary_returns_json_when_a_service_is_down(monkeypatch) -> None:
    module = _load_ops_console()
    client = TestClient(module.app)

    async def _safe_get(_client, url, role=None):  # noqa: ARG001
        if "query-api" in url:
            return {"status": "down", "url": url}
        return {"status": "ok", "url": url}

    monkeypatch.setattr(module, "_safe_get", _safe_get)

    response = client.get("/api/health-summary")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "degraded"
    assert body["up"] < body["total"]
    assert "checks" in body


def test_run_simulation_forwards_downstream_status(monkeypatch) -> None:
    module = _load_ops_console()
    client = TestClient(module.app)
    upstream = _DummyResponse(429, {"detail": "rate limit"})

    monkeypatch.setattr(module.httpx, "AsyncClient", lambda timeout=None: _DummyAsyncClient(post_response=upstream))

    response = client.post("/api/run-simulation", json={"subjects": 2, "days": 7, "profile": "healthy"})
    assert response.status_code == 429
    assert response.json()["detail"] == "rate limit"


def test_governance_review_returns_502_on_connector_error(monkeypatch) -> None:
    module = _load_ops_console()
    client = TestClient(module.app)
    error = httpx.ConnectError("governor unreachable", request=httpx.Request("POST", "http://example.test"))

    monkeypatch.setattr(module.httpx, "AsyncClient", lambda timeout=None: _DummyAsyncClient(post_error=error))

    response = client.post(
        "/api/governance-review",
        json={
            "proposal_id": "demo-123",
            "proposal_type": "schema_change",
            "summary": "Add a hydration metric extension.",
            "impact_scope": "medium",
            "adoption_benefit": 8,
            "implementation_cost": 4,
            "community_impact": 7,
            "security_risk": 3,
            "backward_compatible": True,
        },
    )
    assert response.status_code == 502
    assert response.json()["detail"] == "Governance service unavailable"
