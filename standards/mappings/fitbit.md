# Mapping: Fitbit -> OpenPulse

| Fitbit endpoint family | OpenPulse metric_code | Notes |
|---|---|---|
| activities/heart + intraday | heart_rate | supports 1sec/1min detail depending context |
| activities/steps intraday | steps | minute-level intraday available |
| sleep | sleep_duration/sleep_stage | stages in extension payload |
| spo2 | spo2 | optional based on device support |
| subscription webhook events | source_payload triggers | used for incremental pulls |
