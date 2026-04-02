# OpenPulse Standard

OpenPulse Standard is an open data standard and reference platform for wearable and sensor data.

It gives manufacturers, health systems, analytics teams, and software vendors a practical way to move data from fragmented device ecosystems into one normalized model that is easy to query, govern, and integrate.

## What problem this solves
Today, every wearable integration becomes its own project:
- different APIs
- different units
- different timestamp behavior
- different consent models
- different data quality issues
- different downstream mappings into analytics and clinical workflows

OpenPulse reduces that repeated work.

Instead of building a custom pipeline for every new device or manufacturer, teams can ingest data once, normalize it into a common model, preserve source provenance, and make it available for analytics, monitoring, and EHR export.

## Why adopt now
- Wearable data volume is growing faster than most integration teams can support.
- Health systems need a safer way to separate raw device data from what belongs in the clinical record.
- Manufacturers need a lower-friction path into provider and analytics ecosystems.
- AI and analytics teams need clean, longitudinal, queryable data instead of vendor-specific payloads.

OpenPulse gives all four groups a shared foundation.

## What you can run today
This repo already runs a working local platform with:
- ingestion APIs
- manufacturer simulators for Apple HealthKit, Android Health Connect, Fitbit, Garmin, Oura, WHOOP, Withings, and Dexcom
- normalization into the OpenPulse model
- raw payload lineage storage
- ClickHouse analytics tables and views
- SQL query APIs
- FHIR-aligned export APIs
- governance workflows
- monitoring dashboards
- a live web demo surface

## Time to value
A technically capable team can get value from OpenPulse quickly.

In the current reference implementation you can:
1. start the full stack locally
2. ingest realistic data from all required ecosystems
3. inspect normalized records and lineage
4. run SQL queries over the canonical model
5. review a web demo for operators and stakeholders

That means you can validate the standard, the warehouse model, the API layer, and the demo workflow before committing to a large integration program.

## What makes OpenPulse commercially viable
OpenPulse is designed to be useful in real buying and implementation cycles, not just in architecture diagrams.

It is built to:
- lower integration cost across manufacturers
- preserve manufacturer-specific value through controlled extensions
- support local deployment and data ownership
- provide clean handoffs to analytics and AI teams
- support health-system governance and consent enforcement
- align with FHIR for export without forcing FHIR complexity into the core ingest pipeline

## Why this stack
- **Backend/services**: Python + FastAPI for maintainable APIs and fast adapter delivery.
- **Streaming**: Redpanda for Kafka-compatible ingestion without heavy local ops overhead.
- **Warehouse**: ClickHouse for fast time-series and analytical SQL.
- **Bronze storage**: MinIO for immutable raw payload retention and lineage.
- **Observability**: Prometheus + Grafana for service and pipeline visibility.

## Architecture
- `standards/`: canonical schemas, taxonomy, mappings, compatibility policy
- `services/ingestion-gateway`: ingest, idempotency, rate limiting
- `services/connector-service`: adapters and synthetic generators
- `services/normalization-service`: normalization, provenance, quality scoring
- `services/consent-identity-service`: consent and pseudonymization
- `services/query-api`: operator and analytics access
- `services/ehr-integration`: FHIR-aligned exports and bulk export patterns
- `services/governance-agent`: policy-based approval engine
- `services/ops-console`: operator-facing demo and admin surface
- `data-platform/`: warehouse DDL, marts, lineage-ready structures
- `observability/`: dashboards and metrics config
- `k8s/`: Kubernetes deployment path

## Quickstart
### Docker Desktop
```powershell
Copy-Item .env.example .env
./scripts/bootstrap.ps1
```

### WSL Docker Engine, no Docker Desktop sign-in
```powershell
Copy-Item .env.example .env
./scripts/openpulse-up-wsl.ps1
./scripts/openpulse-status-wsl.ps1
```

The WSL-based path uses open-source Docker Engine inside Ubuntu WSL2.

## Endpoints
### Docker Desktop mode
- Ingestion: `http://localhost:8001`
- Connectors: `http://localhost:8002`
- Query API: `http://localhost:8003`
- Consent: `http://localhost:8004`
- Governor Jeff: `http://localhost:8005`
- EHR integration: `http://localhost:8006`
- Ops console: `http://localhost:8007`
- Grafana: `http://localhost:3000`
- Prometheus: `http://localhost:9090`

### WSL Docker Engine mode
Use the IP printed by `./scripts/openpulse-up-wsl.ps1`.

## Example query
```sql
SELECT subject_id, metric_code, avg(value) AS avg_value
FROM openpulse.observation
GROUP BY subject_id, metric_code
ORDER BY subject_id, metric_code;
```

## Who this is for
- device manufacturers that want easier enterprise adoption
- health systems that need a safer wearable-data ingestion model
- digital health vendors building multi-device products
- analytics teams building cohort, quality, and longitudinal models
- AI teams that need normalized feature-ready data

## Licensing
- Spec/docs: CC BY 4.0
- Reference implementation code: Apache-2.0

## Current status
The current repo includes a working local reference implementation with real services, real tests, real schemas, and a functioning demo path. It is not just a placeholder project.
