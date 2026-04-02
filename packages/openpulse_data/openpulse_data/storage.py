from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO

import boto3

from .settings import settings


class BronzeStorage:
    def __init__(self) -> None:
        self._client = boto3.client(
            "s3",
            endpoint_url=f"http://{settings.minio_endpoint}",
            aws_access_key_id=settings.minio_access_key,
            aws_secret_access_key=settings.minio_secret_key,
            region_name="us-east-1",
        )

    def put_json(self, manufacturer: str, envelope_id: str, payload: bytes) -> str:
        now = datetime.now(tz=timezone.utc)
        key = f"manufacturer={manufacturer}/dt={now:%Y-%m-%d}/hour={now:%H}/{envelope_id}.json"
        self._client.upload_fileobj(BytesIO(payload), settings.minio_bucket_bronze, key)
        return f"s3://{settings.minio_bucket_bronze}/{key}"
