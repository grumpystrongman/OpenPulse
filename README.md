# OpenPulse Standard

OpenPulse Standard is an open protocol + reference implementation for ingesting heterogeneous wearable/sensor data into a canonical open schema and local analytics platform.

## Why this stack
- **Backend/services**: Python + FastAPI for maintainable API-heavy services and rapid adapter implementation.
- **Streaming**: Redpanda (Kafka API compatible) for local-first stream processing with minimal ops overhead.
- **Warehouse**: ClickHouse for high-performance time-series + analytical SQL at local developer scale and commercial viability.
- **Bronze object storage**: MinIO S3-compatible bucket for immutable source payload lineage.
- **Observability**: Prometheus + Grafana dashboards.

## Architecture domains
- `standards/`: canonical schemas, taxonomy, mapping docs.
- `services/ingestion-gateway`: auth, idempotency, rate limiting, ingest API.
- `services/connector-service`: manufacturer adapters + synthetic generators.
- `services/normalization-service`: transform/validate/enrich/provenance.
- `services/consent-identity-service`: consent and pseudonymization.
- `services/query-api`: operator analytics API + cohort endpoints.
- `services/ehr-integration`: FHIR-aligned export patterns.
- `services/governance-agent`: `openpulse-governor-jeff` policy engine.
- `services/ops-console`: operations dashboard.
- `data-platform/`: ClickHouse DDL, bronze/silver/gold model definitions.
- `observability/`: Prometheus + Grafana provisioning.
- `k8s/`: Kubernetes deployment path.

## Quickstart (Docker Desktop)
```powershell
cp .env.example .env
./scripts/bootstrap.ps1
```

Endpoints:
- Ingestion: `http://localhost:8001`
- Connectors/simulators: `http://localhost:8002`
- Query API: `http://localhost:8003`
- Consent/identity: `http://localhost:8004`
- Governor Jeff: `http://localhost:8005`
- EHR integration: `http://localhost:8006`
- Ops console: `http://localhost:8007`
- Grafana: `http://localhost:3000` (admin/admin)
- Prometheus: `http://localhost:9090`

## Quickstart (No Docker Desktop License / WSL Docker Engine)
This path uses open-source Docker Engine inside Ubuntu WSL2, no Docker Desktop sign-in required.

```powershell
Copy-Item .env.example .env
./scripts/openpulse-up-wsl.ps1
./scripts/openpulse-status-wsl.ps1
```

Use the WSL IP printed by `openpulse-up-wsl.ps1` (for example `http://172.x.x.x:8007`).

## Thin vertical slice (implemented)
1. `connector-service` synthetic Fitbit/Apple/Garmin/... payload generation.
2. `ingestion-gateway` envelope + idempotency + Kafka publish.
3. `normalization-service` canonical mapping + quality/provenance + bronze/silver load.
4. `query-api` SQL/cohort/timeline retrieval.
5. `ops-console` visibility and governance decisions.
6. End-to-end test scenario included under `tests/e2e`.

## SQL self-service
Use ClickHouse directly:
```sql
SELECT subject_id, metric_code, avg(value) AS avg_value
FROM openpulse.observation
GROUP BY subject_id, metric_code
ORDER BY subject_id, metric_code;
```

## Branching and release strategy
- `main`: always releasable.
- `release/x.y`: stabilization branches.
- feature branches: `feat/<domain>-<short-name>`.
- tags: `vX.Y.Z`.
- release checklist documented in `docs/release-notes.md`.

## License recommendation
- Spec/docs: CC BY 4.0.
- Reference implementation code: Apache-2.0.

## Current status
- Working local stack and canonical pipeline implemented.
- Manufacturer simulators implemented for all required ecosystems.
- Governance, mapping matrix, FHIR export, observability, and conformance tests included.
