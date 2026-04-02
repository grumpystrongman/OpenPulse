# Manufacturer Capability Matrix (Official Source Survey)

Last reviewed: 2026-04-02

| Manufacturer | Official docs | Auth model | Data access model | Notable metrics confirmed | Update behavior / quirks | OpenPulse mapping risk |
|---|---|---|---|---|---|---|
| Apple HealthKit | https://developer.apple.com/documentation/healthkit/workouts-and-activity-rings, https://developer.apple.com/documentation/healthkit/hkquantitytypeidentifier/heartratevariabilitysdnn, https://developer.apple.com/documentation/swiftui/view/healthdataaccessrequest%28store%3Asharetypes%3Areadtypes%3Atrigger%3Acompletion%3A%29 | On-device HealthKit permissions + app entitlements | Local app read/write APIs; no direct cloud partner REST feed | Workouts, HRV SDNN, heart-rate and many quantity/category types | Per-device/user permissioning and background delivery constraints | Medium (mobile relay required) |
| Android Health Connect | https://developer.android.com/health-and-fitness/health-connect/data-and-data-types/data-types, https://developer.android.com/health-and-fitness/health-connect/rate-limiting, https://developer.android.com/health-and-fitness/health-connect/ui/permissions | Runtime Android health permissions + Play declaration | On-device data broker with read/write APIs and changelog sync | Heart rate, steps, sleep sessions, calories, weight, many more | Foreground/background rate limits; strict permission UX expectations | Medium (mobile relay required) |
| Fitbit Web API | https://dev.fitbit.com/build/reference/web-api/, https://dev.fitbit.com/build/reference/web-api/intraday/get-heartrate-intraday-by-date-range/, https://dev.fitbit.com/build/reference/web-api/intraday/get-activity-intraday-by-date-range/, https://dev.fitbit.com/build/reference/web-api/client-credentials/ | OAuth2 | REST polling + subscription webhooks | Intraday HR/steps/activity, sleep, SpO2, HRV, temperature, subscriptions | Intraday access restrictions and 24h windows for intraday queries | Low |
| Garmin Connect Health API | https://developer.garmin.com/gc-developer-program/health-api/, https://developer.garmin.com/health-sdk/overview/ | Partner onboarding/licensing; consented user connections | REST JSON with push or pull architecture options | Steps, heart rate, sleep, stress, pulse ox, body battery, respiration, BP | Program approval and potential commercial licensing requirements | Medium |
| Oura API v2 | https://cloud.ouraring.com/docs/authentication | OAuth2 / personal access token scope model | REST polling for usercollection endpoints | Sleep, readiness, HR/HRV, sessions/workouts, SpO2 scope | Scope-granular access and daily/timeseries mix | Low |
| WHOOP API | https://developer.whoop.com/api/, https://developer.whoop.com/docs/developing/user-data/recovery/, https://developer.whoop.com/docs/developing/webhooks/ | OAuth2 with scoped access | REST + webhook events | Recovery, sleep, cycle/strain, HRV, RHR; webhook updates | Recovery tied to sleep/cycle workflows; event-driven updates | Low |
| Withings API | https://developer.withings.com/, https://developer.withings.com/developer-guide/v3/withings-solutions/app-to-app-solution/, https://developer.withings.com/sdk/v2/tree/overview/end-user-consent/, https://developer.withings.com/developer-guide/v3/withings-solutions/security-and-compliance | OAuth2 + partner credentials | API/webservice access with webhook notifications in partner flows | Body composition, blood pressure, sleep, activity and device ecosystem data | Partner plan differences; public vs contracted capabilities | Medium |
| Dexcom API v3 | https://developer.dexcom.com/docs, https://developer.dexcom.com/docs/dexcom/authentication/, https://developer.dexcom.com/docs/dexcomv3/endpoint-overview/, https://developer.dexcom.com/docs/dexcomv2/operation/getEstimatedGlucoseValuesV2/ | OAuth2 + user HIPAA authorization | REST endpoints with regional base URLs | EGV/CGM values, calibrations, events, devices, dataRange | Production access tiers and regional endpoints; strict token handling | Low |

## Compatibility and Lossiness Matrix

| Canonical metric | Apple | Android HC | Fitbit | Garmin | Oura | WHOOP | Withings | Dexcom | Lossiness |
|---|---|---|---|---|---|---|---|---|---|
| heart_rate | Y | Y | Y | Y | Y | Y | Partial | N | Low |
| hrv_rmssd | Y | Partial | Y | Partial | Y | Y | N | N | Medium |
| sleep_duration/stages | Y | Y | Y | Y | Y | Y | Y | N | Low |
| steps | Y | Y | Y | Y | N | Partial | Partial | N | Medium |
| stress/recovery/readiness | Partial | N | Partial | Y | Y | Y | N | N | Medium |
| spo2 | Partial | Partial | Y | Y | Partial | Partial | Partial | N | Medium |
| blood_pressure | N | Partial | N | Y | N | N | Y | N | Medium |
| body composition | Partial | Partial | Y | Y | N | N | Y | N | Low |
| glucose | N | N | Partial | N | N | N | N | Y | Low |

## Extension Recommendations

1. `openpulse.ext.garmin`: body battery detail, advanced beat-to-beat streams, stress epochs.
2. `openpulse.ext.whoop`: cycle-specific strain decomposition and sleep-performance contributors.
3. `openpulse.ext.oura`: readiness contributors and temperature deviation context.
4. `openpulse.ext.dexcom`: trend arrows, calibration states, sensor lifecycle markers.
5. `openpulse.ext.withings`: device-program metadata and cloud environment provenance.

## Manufacturer Capability Registry Path
- Runtime registry: `packages/openpulse_core/openpulse_core/manufacturer_registry.py`
- Schema: `standards/schemas/json/manufacturer-capability-1.0.0.schema.json`
