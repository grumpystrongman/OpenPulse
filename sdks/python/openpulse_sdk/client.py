from __future__ import annotations

from typing import Any

import httpx


class OpenPulseClient:
    def __init__(self, base_url: str = "http://localhost:8003") -> None:
        self.base_url = base_url.rstrip("/")
        self._client = httpx.Client(timeout=20.0)

    def observations(self, subject_id: str | None = None, metric_code: str | None = None, limit: int = 200) -> list[dict[str, Any]]:
        params = {"limit": limit}
        if subject_id:
            params["subject_id"] = subject_id
        if metric_code:
            params["metric_code"] = metric_code
        response = self._client.get(f"{self.base_url}/v1/observations", params=params)
        response.raise_for_status()
        return response.json()

    def timeline(self, subject_id: str, from_date: str, to_date: str) -> list[dict[str, Any]]:
        response = self._client.get(
            f"{self.base_url}/v1/timeline/{subject_id}",
            params={"from_date": from_date, "to_date": to_date},
        )
        response.raise_for_status()
        return response.json()

    def run_sql(self, sql: str) -> dict[str, Any]:
        response = self._client.post(f"{self.base_url}/v1/sql", json={"sql": sql})
        response.raise_for_status()
        return response.json()
