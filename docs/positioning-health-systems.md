# Why Health Systems Should Adopt

Health systems need a better way to work with wearable and patient-generated device data.

The current pattern is usually expensive and unsafe at the same time: one-off integrations, unclear provenance, too much raw data pushed toward the chart, and no clean operating model for analytics teams.

OpenPulse provides a cleaner alternative.

## What OpenPulse gives health systems
- one normalized model across multiple manufacturers
- clear separation between raw payload retention and normalized analytics use
- source provenance on every normalized fact
- consent-aware ingestion and identity controls
- local deployment and direct SQL access
- FHIR-aligned export for data that should move into clinical workflows

## Why adopt now
Wearable data is already entering care programs, remote monitoring programs, wellness initiatives, and analytics pipelines.

What many health systems still lack is a shared ingestion and governance layer.

OpenPulse fills that gap by giving teams a practical standard for:
- integration
- normalization
- lineage
- operator visibility
- downstream export

## Time to value
With the current reference stack, a health system team can quickly validate:
1. local deployment
2. multi-manufacturer ingestion
3. normalized observations and lineage
4. cohort and timeline queries
5. FHIR-aligned export patterns
6. operator-facing demo workflows

That makes OpenPulse useful for architecture review, pilot evaluation, and implementation planning right away.

## What you can run today
This repo already supports:
- local stack startup
- simulated data for Apple HealthKit, Android Health Connect, Fitbit, Garmin, Oura, WHOOP, Withings, and Dexcom
- queryable normalized warehouse tables
- APIs for observations, timelines, cohorts, and ad hoc SQL
- FHIR-aligned export endpoints
- dashboards for service health and operations

## What belongs in OpenPulse vs the medical record
OpenPulse is built around a practical rule:
- keep high-volume wearable streams in a longitudinal data platform
- move only the clinically appropriate summaries or events into EHR workflows

That protects chart quality while still making the data useful.

## Why this is commercially useful
OpenPulse helps health systems avoid repeated vendor-by-vendor integration work.

It creates a common platform that can serve:
- digital health programs
- research teams
- data science teams
- remote monitoring programs
- enterprise architecture teams

Instead of funding a separate ingestion pattern for each device ecosystem, teams can use one shared foundation.

## Bottom line
OpenPulse helps health systems move faster on wearable data without sacrificing governance, provenance, or flexibility.
