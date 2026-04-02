from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ManufacturerCapability:
    manufacturer: str
    auth_model: str
    ingestion_mode: str
    supported_metrics: tuple[str, ...]
    update_frequency: str
    quirks: tuple[str, ...]


CAPABILITY_REGISTRY: dict[str, ManufacturerCapability] = {
    "apple_healthkit": ManufacturerCapability(
        manufacturer="apple_healthkit",
        auth_model="On-device authorization and app entitlements",
        ingestion_mode="Batch export / app relay",
        supported_metrics=("heart_rate", "hrv_rmssd", "sleep_duration", "steps", "energy_burned"),
        update_frequency="Near-real-time on sync",
        quirks=("Records are timezone-sensitive", "Duplicate samples possible after re-sync"),
    ),
    "android_health_connect": ManufacturerCapability(
        manufacturer="android_health_connect",
        auth_model="On-device permission grants",
        ingestion_mode="Read APIs from Android app",
        supported_metrics=("heart_rate", "sleep_duration", "steps", "energy_burned"),
        update_frequency="Near-real-time on app sync",
        quirks=("Records may be backfilled", "Origin package changes"),
    ),
    "fitbit": ManufacturerCapability(
        manufacturer="fitbit",
        auth_model="OAuth2",
        ingestion_mode="REST polling + subscriptions",
        supported_metrics=("heart_rate", "steps", "sleep_duration", "energy_burned", "respiratory_rate"),
        update_frequency="1 min intraday for approved scopes",
        quirks=("Intraday access may require review", "Rate limits per user/app"),
    ),
    "garmin": ManufacturerCapability(
        manufacturer="garmin",
        auth_model="Partner API keys + OAuth depending on program",
        ingestion_mode="Push + pull partner APIs",
        supported_metrics=("heart_rate", "stress_score", "spo2", "body_battery", "sleep_duration", "steps"),
        update_frequency="Near-real-time to periodic",
        quirks=("Partner onboarding required", "Payload structures vary by endpoint"),
    ),
    "oura": ManufacturerCapability(
        manufacturer="oura",
        auth_model="OAuth2 or personal access token",
        ingestion_mode="REST polling",
        supported_metrics=("sleep_duration", "readiness_score", "hrv_rmssd", "heart_rate", "temperature"),
        update_frequency="Daily summaries + detailed timeseries",
        quirks=("Day rollups include timezone offset", "Tagged contributors for temperature variation"),
    ),
    "whoop": ManufacturerCapability(
        manufacturer="whoop",
        auth_model="OAuth2",
        ingestion_mode="REST polling + webhooks",
        supported_metrics=("recovery_score", "strain_score", "sleep_duration", "heart_rate", "hrv_rmssd"),
        update_frequency="Multiple updates daily",
        quirks=("Cycle windows can overlap daily boundaries", "Recovery updates after sleep processing"),
    ),
    "withings": ManufacturerCapability(
        manufacturer="withings",
        auth_model="OAuth2",
        ingestion_mode="REST notifications + polling",
        supported_metrics=("body_weight", "body_fat_percent", "blood_pressure_systolic", "blood_pressure_diastolic", "sleep_duration"),
        update_frequency="Device sync-driven",
        quirks=("Measure type codes map to multiple units", "Timezone offsets explicit in payload"),
    ),
    "dexcom": ManufacturerCapability(
        manufacturer="dexcom",
        auth_model="OAuth2",
        ingestion_mode="REST polling",
        supported_metrics=("glucose",),
        update_frequency="Typically 5-minute cadence",
        quirks=("Sensor warm-up gaps", "Calibration/state markers in payload"),
    ),
}
