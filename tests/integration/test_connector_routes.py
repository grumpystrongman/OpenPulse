import importlib.util
from pathlib import Path

from fastapi.testclient import TestClient


def _load_connector_app():
    path = Path("services/connector-service/app/main.py")
    spec = importlib.util.spec_from_file_location("connector_main_for_routes", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


def test_simulate_all_route_exists(monkeypatch) -> None:
    module = _load_connector_app()

    async def _noop_run_simulation(*args, **kwargs):  # noqa: ANN002, ANN003
        return None

    monkeypatch.setattr(module, "_run_simulation", _noop_run_simulation)
    client = TestClient(module.app)
    response = client.post("/v1/simulate-all", params={"subjects": 1, "days": 1, "profile": "healthy"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "started"
    assert "manufacturers" in payload
