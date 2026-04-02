# Data Platform Model

## Bronze
- Raw envelope JSON stored in MinIO (`openpulse-bronze`) and mirrored in `openpulse.source_payload`.

## Silver
- Canonical normalized observations in `openpulse.observation` with provenance in `openpulse.provenance_link`.

## Gold
- Daily marts and feature-ready aggregates (e.g., `gold_daily_subject_metrics`, `gold_subject_daily_recovery`).

## Lineage
- `source_payload.payload_hash` + `provenance_link` connects every fact to origin payload.
- `normalization_run` tracks transformation run health and reject counts.

## Data Quality
- `quality_assessment` captures quality, completeness, and confidence dimensions.
- `failed_record_queue` + replay script supports operational recovery.
