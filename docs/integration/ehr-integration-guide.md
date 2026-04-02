# EHR Integration Guide

## Scope
This guide describes exporting OpenPulse normalized data into EHR-adjacent workflows without forcing all inbound events into the medical record.

## Recommended pattern
1. Keep complete wearable stream in OpenPulse analytics lakehouse.
2. Publish clinically relevant summaries/events to EHR-facing integration layer.
3. Preserve full provenance and confidence scoring with every export.

## FHIR-aligned export
Use `services/ehr-integration`:
- `GET /v1/fhir/observations/{subject_id}`
- `GET /v1/export/bulk`

## Epic-oriented pattern
- Use OpenPulse as intermediary longitudinal monitoring service.
- Send curated Observation/Device resources through integration engine.
- Keep high-frequency raw streams outside chart unless explicitly clinically reviewed.

## Cerner/Oracle Health pattern
- Use event subscriptions for alert-grade thresholds.
- Use nightly bulk export for trend summaries and quality metadata.

## Guardrails
- Do write clinically validated, consented, quality-scored summaries.
- Do not write noisy raw minute-level data directly into chart by default.
- Always preserve manufacturer provenance and quality score.

## PGHD workflow
1. Patient consents in app.
2. Data ingested and normalized in OpenPulse.
3. Clinical rule filters export candidates.
4. EHR receives FHIR bundle with attribution and confidence.
