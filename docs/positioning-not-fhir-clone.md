# Why OpenPulse Is Not a FHIR Clone

OpenPulse aligns with FHIR where that helps adoption. It does not copy FHIR into the center of the platform.

That difference matters.

## What OpenPulse is trying to solve
Wearable and sensor data arrives as:
- high-frequency observations
- device-specific payloads
- inconsistent units and timestamps
- large longitudinal streams
- analytics-heavy workloads

FHIR was not designed to be the best internal format for that entire pipeline.

## What OpenPulse does differently
OpenPulse uses a simpler internal model optimized for:
- ingesting large volumes of device data
- preserving provenance and original payloads
- normalizing common metrics across manufacturers
- supporting warehouse analytics and feature generation
- exporting the right subset into FHIR-aligned structures when needed

## Why that is better in practice
If a team forces all raw wearable data into FHIR-shaped internal pipelines, it often creates:
- unnecessary implementation complexity
- slower ingestion and transformation work
- harder analytics workflows
- more cost with little added value

OpenPulse avoids that by keeping the core event and warehouse model straightforward.

## Where FHIR fits
FHIR still matters.

OpenPulse uses FHIR where it makes sense:
- export into clinical workflows
- integration with EHR-adjacent systems
- standards alignment for data that belongs in a clinical exchange context

That is a practical integration strategy, not a rejection of FHIR.

## What you can run today
The reference implementation already includes:
- normalized internal observation tables
- FHIR-aligned export endpoints
- guidance on what should and should not move into the chart
- example integration patterns for health-system adopters

## Bottom line
OpenPulse is built for wearable interoperability and analytics first, with FHIR used as an export and alignment layer where appropriate. That is why it is more practical than simply turning the project into another FHIR-shaped ingestion stack.
