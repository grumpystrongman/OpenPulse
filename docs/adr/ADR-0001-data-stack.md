# ADR-0001: Data Platform Choice

Date: 2026-04-02

## Decision
Use ClickHouse + Redpanda + MinIO as the default local and production-path open stack.

## Rationale
- ClickHouse excels at time-series analytics and cohort queries over billions of events.
- Redpanda gives Kafka compatibility with simpler local operations than full Kafka + ZooKeeper/KRaft clusters.
- MinIO provides S3-compatible raw bronze retention and lineage-friendly immutable object storage.

## Consequences
- SQL analytics and materialized views become first-class.
- Kafka ecosystem compatibility maintained for future external connectors.
- Object storage contracts are S3 compatible for migration.
