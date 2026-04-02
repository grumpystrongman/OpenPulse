from __future__ import annotations

import os
import re
from collections.abc import Callable

from fastapi import Header, HTTPException

ROLE_ORDER: dict[str, int] = {
    "analyst": 1,
    "integration": 2,
    "operator": 3,
    "admin": 4,
}

IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9_.:-]{1,128}$")
SAFE_SCOPE_PATTERN = re.compile(r"^[A-Za-z0-9_.:/-]{1,128}$")
SAFE_METRIC_PATTERN = re.compile(r"^[A-Za-z0-9_.:-]{1,64}$")
SAFE_CONSENT_ID_PATTERN = re.compile(r"^[A-Fa-f0-9]{32}$")
BLOCKED_SQL_KEYWORDS_RE = re.compile(
    r"\b(insert|update|delete|alter|drop|truncate|attach|detach|optimize|system)\b",
    re.IGNORECASE,
)
LIMIT_SUFFIX_RE = re.compile(r"(?is)\blimit\s+(\d+)\s*$")


def auth_disabled() -> bool:
    return os.getenv("OPENPULSE_AUTH_DISABLED", "false").lower() in {"1", "true", "yes"}


def enforce_role(required_role: str, role_header: str | None, token_header: str | None) -> str:
    if auth_disabled():
        return role_header or "anonymous"

    role = (role_header or "").strip().lower()
    if not role:
        raise HTTPException(status_code=401, detail="Missing X-OpenPulse-Role header")
    if role not in ROLE_ORDER:
        raise HTTPException(status_code=403, detail=f"Unsupported role: {role}")

    required_order = ROLE_ORDER.get(required_role, 999)
    if ROLE_ORDER[role] < required_order:
        raise HTTPException(status_code=403, detail=f"Role '{role}' cannot access this endpoint")

    expected_token = os.getenv("OPENPULSE_AUTH_TOKEN", "").strip()
    if expected_token and token_header != expected_token:
        raise HTTPException(status_code=401, detail="Invalid X-OpenPulse-Token")

    return role


def role_dependency(required_role: str) -> Callable[..., str]:
    def _check_role(
        x_openpulse_role: str | None = Header(default=None, alias="X-OpenPulse-Role"),
        x_openpulse_token: str | None = Header(default=None, alias="X-OpenPulse-Token"),
    ) -> str:
        return enforce_role(required_role=required_role, role_header=x_openpulse_role, token_header=x_openpulse_token)

    return _check_role


def validate_identifier(value: str, field: str, pattern: re.Pattern[str] = IDENTIFIER_PATTERN) -> str:
    if not pattern.fullmatch(value):
        raise HTTPException(status_code=400, detail=f"Invalid {field}")
    return value


def require_role(required_role: str) -> Callable[..., str]:
    return role_dependency(required_role)


def sql_quote(value: str) -> str:
    return value.replace("'", "''")


def clamp_int(value: int, *, minimum: int, maximum: int, field_name: str) -> int:
    if value < minimum or value > maximum:
        raise HTTPException(status_code=400, detail=f"{field_name} must be between {minimum} and {maximum}")
    return value


def sanitize_select_sql(sql: str, max_rows: int = 5000) -> str:
    normalized = sql.strip()
    if not normalized.lower().startswith("select"):
        raise HTTPException(status_code=400, detail="Only SELECT statements are allowed")
    if ";" in normalized.rstrip(";"):
        raise HTTPException(status_code=400, detail="Multiple statements are not allowed")
    if BLOCKED_SQL_KEYWORDS_RE.search(normalized):
        raise HTTPException(status_code=400, detail="Statement contains blocked keywords")
    normalized = normalized.rstrip(";")
    match = LIMIT_SUFFIX_RE.search(normalized)
    if match:
        limit_value = min(int(match.group(1)), max_rows)
        normalized = LIMIT_SUFFIX_RE.sub(f"LIMIT {limit_value}", normalized, count=1)
    else:
        normalized = f"{normalized} LIMIT {max_rows}"
    return normalized


def validate_subject_id(value: str) -> str:
    return validate_identifier(value, "subject_id")


def validate_scope(value: str) -> str:
    return validate_identifier(value, "scope", SAFE_SCOPE_PATTERN)


def validate_metric_code(value: str) -> str:
    return validate_identifier(value, "metric_code", SAFE_METRIC_PATTERN)


def validate_consent_id(value: str) -> str:
    return validate_identifier(value, "consent_id", SAFE_CONSENT_ID_PATTERN)
