from __future__ import annotations

from hashlib import sha256


def payload_hash(raw_payload: str) -> str:
    return sha256(raw_payload.encode("utf-8")).hexdigest()
