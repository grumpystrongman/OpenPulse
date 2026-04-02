# Mapping: Dexcom -> OpenPulse

| Dexcom endpoint | OpenPulse metric_code | Notes |
|---|---|---|
| /users/self/egvs | glucose | `mg/dL` canonical, trend in extension |
| /users/self/devices | device metadata | serialized into device + source payload lineage |
| /users/self/dataRange | normalization windowing | helps backfill planning |
| /users/self/events | therapy events (future) | extension pathway for insulin/carb events |
