# Mapping: Android Health Connect -> OpenPulse

| Health Connect record | OpenPulse metric_code | Notes |
|---|---|---|
| HeartRateRecord | heart_rate | sample BPM normalized to `beats/min` |
| StepsRecord | steps | count passthrough |
| SleepSessionRecord | sleep_duration/sleep_stage | intervals map to session and stage extension |
| TotalCaloriesBurnedRecord | energy_burned | calories normalized to `kcal` |
