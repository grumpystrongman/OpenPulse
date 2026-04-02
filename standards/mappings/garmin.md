# Mapping: Garmin -> OpenPulse

| Garmin Health JSON fields | OpenPulse metric_code | Notes |
|---|---|---|
| heartRate | heart_rate | direct |
| stressLevel | stress_score | normalized score |
| pulseOx / spo2 | spo2 | percentage |
| bodyBattery | body_battery | manufacturer-specific canonical metric |
| steps / calories / sleep summary | steps, energy_burned, sleep_duration | direct + extensions |
