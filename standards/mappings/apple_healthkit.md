# Mapping: Apple HealthKit -> OpenPulse

- Source shape: `HKQuantityTypeIdentifier*`, `HKCategoryTypeIdentifier*`, `HKWorkout` objects.
- Ingest mode in reference stack: app relay or synthetic feed.

| HealthKit sample | OpenPulse metric_code | Notes |
|---|---|---|
| HKQuantityTypeIdentifierHeartRate | heart_rate | `count/min` -> `beats/min` |
| HKQuantityTypeIdentifierHeartRateVariabilitySDNN | hrv_rmssd | native in `ms` |
| HKCategoryTypeIdentifierSleepAnalysis | sleep_duration/sleep_stage | stage mapping in extension payload |
| HKWorkout | activity/session | workout metadata mapped to `activity` + `session` |
