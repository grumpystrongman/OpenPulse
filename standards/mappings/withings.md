# Mapping: Withings -> OpenPulse

| Withings measure type / flow | OpenPulse metric_code | Notes |
|---|---|---|
| type 1 (weight) | body_weight | `value * 10^unit` to kg |
| type 6 (fat ratio) | body_fat_percent | percentage |
| type 9/10 (BP) | blood_pressure_systolic/diastolic | clinical-grade flag |
| sleep and activity services | sleep_duration / steps / energy_burned | endpoint-specific mappings |
