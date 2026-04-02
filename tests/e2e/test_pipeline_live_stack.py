from __future__ import annotations

import os
import time

import httpx
import pytest

REQUIRED_MANUFACTURERS = {
    "apple_healthkit",
    "android_health_connect",
    "fitbit",
    "garmin",
    "oura",
    "whoop",
    "withings",
    "dexcom",
}


def _base_url() -> str:
    return os.getenv("OPENPULSE_BASE_URL", "http://localhost")


def _auth_headers(role: str) -> dict[str, str]:
    headers = {"X-OpenPulse-Role": role}
    token = os.getenv("OPENPULSE_AUTH_TOKEN", "").strip()
    if token:
        headers["X-OpenPulse-Token"] = token
    return headers


@pytest.mark.skipif(
    os.getenv("OPENPULSE_LIVE_E2E", "0").lower() not in {"1", "true", "yes"},
    reason="Set OPENPULSE_LIVE_E2E=1 to run distributed live-stack e2e test",
)
def test_live_stack_pipeline_end_to_end() -> None:
    base = _base_url()
    with httpx.Client(timeout=30.0) as client:
        health = client.get(f"{base}:8001/health")
        if health.status_code != 200:
            pytest.skip(f"OpenPulse live stack not reachable at {base}")

        run_start = client.post(
            f"{base}:8002/v1/simulate-all",
            params={"subjects": 1, "days": 2, "profile": "healthy"},
        )
        run_start.raise_for_status()
        run_id = run_start.json()["run_id"]
        assert run_id

        completed = False
        for _ in range(80):
            run_status = client.get(f"{base}:8002/v1/runs/{run_id}")
            run_status.raise_for_status()
            status_payload = run_status.json()
            if status_payload.get("status") in {"completed", "completed_with_errors"}:
                completed = True
                break
            time.sleep(2)

        assert completed, "Simulation run did not complete in time"

        for _ in range(30):
            summary = client.get(f"{base}:8007/api/summary")
            summary.raise_for_status()
            summary_payload = summary.json()
            if summary_payload.get("total_observations", 0) > 0:
                break
            time.sleep(2)

        summary = client.get(f"{base}:8007/api/summary")
        summary.raise_for_status()
        summary_payload = summary.json()
        assert summary_payload["total_observations"] > 0

        rows = client.post(
            f"{base}:8003/v1/sql",
            headers=_auth_headers("operator"),
            json={"sql": "SELECT manufacturer, count() AS c FROM openpulse.observation GROUP BY manufacturer"},
        )
        rows.raise_for_status()
        observed = {row["manufacturer"] for row in rows.json().get("rows", [])}
        assert REQUIRED_MANUFACTURERS.issubset(observed)

        risk = client.get(
            f"{base}:8003/v1/cohorts/top-risk",
            headers=_auth_headers("analyst"),
            params={"limit": 10},
        )
        risk.raise_for_status()
        assert isinstance(risk.json(), list)
