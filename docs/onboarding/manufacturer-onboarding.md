# Manufacturer Onboarding Guide

This guide is for manufacturers, platform teams, and integration partners who want to support the OpenPulse Standard.

## Goal
The goal is simple: make your data easier to adopt without stripping away what makes your platform valuable.

## What success looks like
At the end of onboarding, a downstream team should be able to:
- understand your supported capabilities
- ingest your payloads or events
- normalize your core metrics into OpenPulse
- preserve your attribution and device metadata
- retain your premium or device-specific data through extensions
- verify the integration with conformance tests

## Why do this now?
Every enterprise integration that starts from scratch costs time and slows adoption.

OpenPulse gives you a reusable path so buyers can evaluate and integrate your platform faster.

## Onboarding steps
1. Publish a capability declaration using the `manufacturer-capability` schema.
2. Define your auth model, consent requirements, and access scopes.
3. Map your core metrics into the OpenPulse taxonomy.
4. Identify manufacturer-specific fields that should remain in your extension namespace.
5. Run the conformance kit.
6. Review governance requirements for release inclusion.

## What you can test immediately
Using the current reference stack, you can:
- review mapping documents
- compare normalized records to raw payloads
- inspect provenance links
- validate analytics behavior on the canonical model
- demonstrate how your data appears to health-system and analytics users

## What OpenPulse preserves for you
OpenPulse does not erase manufacturer identity. It preserves:
- manufacturer name
- device metadata
- firmware and app version metadata
- source payload lineage
- controlled vendor extensions

## Recommended adoption path
Start with the shared core metrics that buyers expect first. Then expose higher-value product-specific fields through your extension namespace.

That gives buyers immediate interoperability without forcing you into a lowest-common-denominator product model.

## Time to value
A strong first milestone is not "full production integration." It is a working proof point that shows:
- your data maps cleanly
- provenance is preserved
- the canonical model is usable
- the downstream buyer experience is simpler than a one-off integration

## Bottom line
Manufacturer onboarding in OpenPulse is meant to shorten implementation cycles and increase confidence for downstream adopters.
