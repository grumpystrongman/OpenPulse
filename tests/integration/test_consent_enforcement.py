from __future__ import annotations

import importlib.util
from pathlib import Path

import httpx
from fastapi.testclient import TestClient
import pytest


class _FakeRedis:
    def __init__(self) -> None:
        self._values: dict[str, int] = {}

    def incr(self, key: str) -> int:
        self._values[key] = self._values.get(key, 0) + 1
        return self._values[key]

    def expire(self, key: str, seconds: int) -> bool:  # noqa: ARG002
        return True

    def set(self, name: str, value: str, ex: int | None = None, nx: bool | None = None) -> bool:  # noqa: ARG002
        if nx and name in self._values:
            return False
        self._values[name] = 1
        return True


class _FakeProducer:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def produce(self, topic: str, key: bytes, value: bytes, headers: dict[str, str]) -> None:
        self.calls.append({"topic": topic, "key": key, "value": value, "headers": headers})

    def flush(self, timeout: float) -> None:  # noqa: ARG002
        return None


class _FakeResponse:
    def __init__(self, status_code: int, payload: dict) -> None:
        self.status_code = status_code
        self._payload = payload
        self.request = httpx.Request("GET", "http://consent-identity-service:8004")

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("error", request=self.request, response=self)

    def json(self) -> dict:
        return self._payload


class _FakeConsentClient:
    def __init__(self, response: _FakeResponse | None = None, error: Exception | None = None) -> None:
        self.response = response
        self.error = error
        self.calls: list[tuple[str, dict | None]] = []

    def __enter__(self) -> "_FakeConsentClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001, D401
        return None

    def get(self, url: str, params: dict | None = None, headers: dict | None = None) -> _FakeResponse:
        self.calls.append((url, params, headers))
        if self.error is not None:
            raise self.error
        assert self.response is not None
        return self.response


@pytest.fixture(autouse=True)
def _clear_auth_token(monkeypatch) -> None:
    monkeypatch.delenv("OPENPULSE_AUTH_TOKEN", raising=False)


def _load_ingestion_app():
    path = Path("services/ingestion-gateway/app/main.py")
    spec = importlib.util.spec_from_file_location("ingestion_gateway_main", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


INGESTION_MODULE = _load_ingestion_app()


def _client(module):
    return TestClient(module.app)


def _headers() -> dict[str, str]:
    return {
        "x-subject-id": "subject-123",
        "x-connection-id": "connection-123",
        "x-idempotency-key": "idem-123",
        "x-device-id": "device-123",
        "x-device-model": "model-123",
        "x-device-firmware": "fw-1.0.0",
        "x-device-app-version": "app-1.0.0",
    }


def test_ingest_requires_allowed_consent(monkeypatch) -> None:
    module = INGESTION_MODULE
    fake_redis = _FakeRedis()
    fake_producer = _FakeProducer()
    fake_consent_client = _FakeConsentClient(_FakeResponse(200, {"allowed": True, "reason": "granted"}))
    monkeypatch.setattr(module, "redis_client", fake_redis)
    monkeypatch.setattr(module, "producer", fake_producer)
    monkeypatch.setattr(module.httpx, "Client", lambda timeout: fake_consent_client)
    monkeypatch.setenv("OPENPULSE_CONSENT_BASE_URL", "http://consent-identity-service:8004")
    client = _client(module)

    response = client.post("/v1/ingest/fitbit", headers=_headers(), json={"steps": 1234})

    assert response.status_code == 200
    assert response.json()["status"] == "accepted"
    assert fake_consent_client.calls == [
        (
            "http://consent-identity-service:8004/v1/consents/check/subject-123",
            {"scope": "ingest:fitbit"},
            {"X-OpenPulse-Role": "integration"},
        )
    ]
    assert len(fake_producer.calls) == 1
    headers = fake_producer.calls[0]["headers"]
    assert headers["consent_allowed"] == "true"
    assert headers["consent_reason"] == "granted"


def test_ingest_rejects_when_consent_denied(monkeypatch) -> None:
    module = INGESTION_MODULE
    fake_redis = _FakeRedis()
    fake_producer = _FakeProducer()
    fake_consent_client = _FakeConsentClient(_FakeResponse(200, {"allowed": False, "reason": "revoked"}))
    monkeypatch.setattr(module, "redis_client", fake_redis)
    monkeypatch.setattr(module, "producer", fake_producer)
    monkeypatch.setattr(module.httpx, "Client", lambda timeout: fake_consent_client)
    client = _client(module)

    response = client.post("/v1/ingest/fitbit", headers=_headers(), json={"steps": 1234})

    assert response.status_code == 403
    assert response.json()["detail"]["reason"] == "revoked"
    assert len(fake_producer.calls) == 0


def test_ingest_rejects_when_consent_service_unavailable(monkeypatch) -> None:
    module = INGESTION_MODULE
    fake_redis = _FakeRedis()
    fake_producer = _FakeProducer()
    fake_error = httpx.ConnectError("connection refused", request=httpx.Request("GET", "http://consent"))
    fake_consent_client = _FakeConsentClient(error=fake_error)
    monkeypatch.setattr(module, "redis_client", fake_redis)
    monkeypatch.setattr(module, "producer", fake_producer)
    monkeypatch.setattr(module.httpx, "Client", lambda timeout: fake_consent_client)
    client = _client(module)

    response = client.post("/v1/ingest/fitbit", headers=_headers(), json={"steps": 1234})

    assert response.status_code == 503
    assert response.json()["detail"] == "Consent service unavailable"
    assert len(fake_producer.calls) == 0
