from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    kafka_bootstrap_servers: str = "localhost:19092"
    kafka_raw_topic: str = "openpulse.raw.ingest"
    kafka_normalized_topic: str = "openpulse.normalized.observation"

    clickhouse_host: str = "localhost"
    clickhouse_port: int = 8123
    clickhouse_user: str = "default"
    clickhouse_password: str = "openpulse"
    clickhouse_database: str = "openpulse"

    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "openpulse"
    minio_secret_key: str = "openpulse123"
    minio_bucket_bronze: str = "openpulse-bronze"
    minio_secure: bool = False

    redis_host: str = "localhost"
    redis_port: int = 6379


settings = Settings()
