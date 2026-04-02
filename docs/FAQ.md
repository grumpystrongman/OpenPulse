# FAQ

## What is OpenPulse?
OpenPulse is an open standard and reference platform for wearable and sensor data. It ingests data from multiple manufacturers, normalizes it into one model, stores it in a local analytics platform, and exposes it through APIs, SQL, and FHIR-aligned export patterns.

## What can I run today?
You can run a working local stack with:
- ingestion services
- manufacturer simulators
- normalization pipelines
- ClickHouse analytics tables
- query APIs
- EHR export APIs
- monitoring dashboards
- an operator-facing demo surface

## Is this only a standard, or is there working software too?
There is working software in this repo. The reference implementation includes real services, real schemas, real tests, and a working local deployment path.

## Is this production-ready?
The repo is production-oriented and commercially relevant, but it is still a reference implementation. It is suitable for pilots, design validation, buyer demonstrations, partner enablement, and as a starting point for hardened deployments.

## Why would a manufacturer use OpenPulse?
Because it lowers repeated integration cost while preserving source attribution, capability declarations, and manufacturer-specific extensions.

## Why would a health system use OpenPulse?
Because it provides a cleaner way to ingest, govern, analyze, and selectively export wearable data without turning every new manufacturer into a separate project.

## Can I query the data directly with SQL?
Yes. ClickHouse is part of the reference stack and the normalized data model is directly queryable.

## Do you support live manufacturer credentials?
The platform is designed for live integrations, but the repo also includes realistic synthetic generators so teams can validate the system without waiting on every credential and partnership step.

## How do extensions work?
OpenPulse normalizes common metrics into an open core model and keeps manufacturer-specific or premium fields in controlled namespaced extensions.

## Does OpenPulse replace FHIR?
No. OpenPulse uses a simpler internal model for ingest and analytics, then provides FHIR-aligned exports for the subset of data that should move into clinical workflows.

## How quickly can I evaluate this?
A capable team can stand up the platform locally, ingest sample data, inspect normalized records, and run queries in a short evaluation cycle.

## What is the strongest reason to adopt OpenPulse?
It gives multiple stakeholders one shared answer to the same problem: how to make wearable data usable without rebuilding the same integration stack for every manufacturer and every downstream team.
