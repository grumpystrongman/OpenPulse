# Health System Onboarding Guide

This guide is for health systems, provider organizations, digital health programs, and enterprise data teams evaluating OpenPulse.

## Goal
Stand up one wearable-data platform that can serve clinical integration, analytics, and operational review without building a separate pipeline for every manufacturer.

## Why adopt now?
Most health systems already have wearable data arriving from somewhere. The real question is whether that data is entering the organization through a governable, reusable, and analytics-friendly path.

OpenPulse is built to provide that path.

## What you can run today
With the current reference stack, you can:
- deploy locally
- ingest multi-manufacturer sample data
- inspect normalized observations and lineage
- run timeline and cohort queries
- review FHIR-aligned export behavior
- show a working demo to architecture, data, and clinical stakeholders

## Recommended onboarding path
1. Deploy the stack locally.
2. Review identity, pseudonymization, and consent policies.
3. Validate the normalized model with simulated multi-manufacturer data.
4. Run operator and analytics queries.
5. Decide what belongs in analytics, monitoring workflows, and EHR export.
6. Pilot with synthetic data before moving toward live device connections.

## Questions to answer during evaluation
- Which wearable programs will this support first?
- Which downstream teams need direct access: analytics, care management, research, app teams?
- Which observations should stay in longitudinal storage versus move into the chart?
- What consent and audit requirements must be enforced?

## What good evaluation looks like
A good evaluation ends with clear answers to four things:
- can we ingest the data reliably?
- can we trust lineage and normalization?
- can our analysts and engineers actually use the model?
- can we safely control what gets exported into clinical workflows?

## Time to value
OpenPulse is useful early in the evaluation cycle because you do not need to wait for every live connection before validating the core design. The included simulators let teams test ingestion, normalization, warehousing, querying, and export patterns immediately.

## Bottom line
Health-system onboarding should produce a real operating model, not just a successful demo. OpenPulse is designed to help teams get there faster.
