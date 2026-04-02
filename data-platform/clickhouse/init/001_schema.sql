CREATE DATABASE IF NOT EXISTS openpulse;

CREATE TABLE IF NOT EXISTS openpulse.subject (
    subject_id String,
    pseudonym_id String,
    created_at DateTime64(3, 'UTC'),
    attributes_json String
) ENGINE = ReplacingMergeTree
ORDER BY (subject_id);

CREATE TABLE IF NOT EXISTS openpulse.consent (
    consent_id String,
    subject_id String,
    scope String,
    status String,
    granted_at DateTime64(3, 'UTC'),
    revoked_at Nullable(DateTime64(3, 'UTC')),
    expires_at Nullable(DateTime64(3, 'UTC')),
    source String,
    policy_version String
) ENGINE = ReplacingMergeTree
ORDER BY (subject_id, consent_id);

CREATE TABLE IF NOT EXISTS openpulse.manufacturer (
    manufacturer_id String,
    name String,
    auth_model String,
    ingestion_mode String,
    capability_json String,
    created_at DateTime64(3, 'UTC')
) ENGINE = ReplacingMergeTree
ORDER BY (manufacturer_id);

CREATE TABLE IF NOT EXISTS openpulse.device (
    device_id String,
    subject_id String,
    manufacturer String,
    model String,
    firmware_version String,
    app_version String,
    linked_at DateTime64(3, 'UTC'),
    metadata_json String
) ENGINE = ReplacingMergeTree
ORDER BY (subject_id, device_id);

CREATE TABLE IF NOT EXISTS openpulse.device_capability (
    device_id String,
    capability_code String,
    value_type String,
    unit String,
    sampling_granularity String,
    declared_at DateTime64(3, 'UTC')
) ENGINE = ReplacingMergeTree
ORDER BY (device_id, capability_code);

CREATE TABLE IF NOT EXISTS openpulse.connection_account (
    connection_id String,
    subject_id String,
    manufacturer String,
    auth_state String,
    token_expiry Nullable(DateTime64(3, 'UTC')),
    created_at DateTime64(3, 'UTC'),
    metadata_json String
) ENGINE = ReplacingMergeTree
ORDER BY (subject_id, connection_id);

CREATE TABLE IF NOT EXISTS openpulse.source_payload (
    envelope_id String,
    manufacturer String,
    subject_id String,
    connection_id String,
    idempotency_key String,
    received_time DateTime64(3, 'UTC'),
    source_endpoint String,
    payload_json String,
    payload_hash String,
    bronze_uri String
) ENGINE = MergeTree
ORDER BY (received_time, manufacturer, subject_id);

CREATE TABLE IF NOT EXISTS openpulse.observation (
    observation_id String,
    envelope_id String,
    subject_id String,
    manufacturer String,
    metric_code String,
    metric_display String,
    value Nullable(Float64),
    value_text Nullable(String),
    unit Nullable(String),
    original_value Nullable(Float64),
    original_unit Nullable(String),
    quality_score Float64,
    completeness_score Float64,
    confidence_score Float64,
    clinical_grade String,
    event_time DateTime64(3, 'UTC'),
    observed_time Nullable(DateTime64(3, 'UTC')),
    device_time Nullable(DateTime64(3, 'UTC')),
    received_time Nullable(DateTime64(3, 'UTC')),
    processed_time Nullable(DateTime64(3, 'UTC')),
    session_id Nullable(String),
    extension_namespace Nullable(String),
    extension_payload_json Nullable(String)
) ENGINE = MergeTree
ORDER BY (subject_id, event_time, metric_code, manufacturer);

CREATE TABLE IF NOT EXISTS openpulse.observation_series (
    series_id String,
    subject_id String,
    manufacturer String,
    metric_code String,
    start_time DateTime64(3, 'UTC'),
    end_time DateTime64(3, 'UTC'),
    sample_count UInt32,
    pointer_uri String,
    quality_score Float64
) ENGINE = MergeTree
ORDER BY (subject_id, metric_code, start_time);

CREATE TABLE IF NOT EXISTS openpulse.session (
    session_id String,
    subject_id String,
    session_type String,
    manufacturer String,
    start_time DateTime64(3, 'UTC'),
    end_time DateTime64(3, 'UTC'),
    metadata_json String
) ENGINE = MergeTree
ORDER BY (subject_id, session_type, start_time);

CREATE TABLE IF NOT EXISTS openpulse.activity (
    activity_id String,
    subject_id String,
    manufacturer String,
    activity_type String,
    start_time DateTime64(3, 'UTC'),
    end_time DateTime64(3, 'UTC'),
    duration_min Float64,
    calories_kcal Nullable(Float64),
    steps Nullable(Float64),
    distance_m Nullable(Float64),
    source_observation_ids Array(String)
) ENGINE = MergeTree
ORDER BY (subject_id, start_time, activity_type);

CREATE TABLE IF NOT EXISTS openpulse.sleep_episode (
    sleep_episode_id String,
    subject_id String,
    manufacturer String,
    start_time DateTime64(3, 'UTC'),
    end_time DateTime64(3, 'UTC'),
    duration_min Float64,
    sleep_score Nullable(Float64),
    stage_summary_json String
) ENGINE = MergeTree
ORDER BY (subject_id, start_time);

CREATE TABLE IF NOT EXISTS openpulse.recovery_state (
    recovery_id String,
    subject_id String,
    manufacturer String,
    event_time DateTime64(3, 'UTC'),
    recovery_score Nullable(Float64),
    readiness_score Nullable(Float64),
    strain_score Nullable(Float64),
    stress_score Nullable(Float64),
    source_observation_ids Array(String)
) ENGINE = MergeTree
ORDER BY (subject_id, event_time);

CREATE TABLE IF NOT EXISTS openpulse.glucose_reading (
    glucose_reading_id String,
    subject_id String,
    manufacturer String,
    event_time DateTime64(3, 'UTC'),
    glucose_mg_dl Float64,
    trend Nullable(String),
    clinical_grade String,
    source_observation_id String
) ENGINE = MergeTree
ORDER BY (subject_id, event_time);

CREATE TABLE IF NOT EXISTS openpulse.body_measurement (
    body_measurement_id String,
    subject_id String,
    manufacturer String,
    event_time DateTime64(3, 'UTC'),
    body_weight_kg Nullable(Float64),
    body_fat_percent Nullable(Float64),
    source_observation_ids Array(String)
) ENGINE = MergeTree
ORDER BY (subject_id, event_time);

CREATE TABLE IF NOT EXISTS openpulse.blood_pressure_reading (
    blood_pressure_id String,
    subject_id String,
    manufacturer String,
    event_time DateTime64(3, 'UTC'),
    systolic_mmhg Float64,
    diastolic_mmhg Float64,
    source_observation_ids Array(String)
) ENGINE = MergeTree
ORDER BY (subject_id, event_time);

CREATE TABLE IF NOT EXISTS openpulse.quality_assessment (
    quality_assessment_id String,
    envelope_id String,
    observation_id Nullable(String),
    score Float64,
    dimensions_json String,
    assessed_at DateTime64(3, 'UTC')
) ENGINE = MergeTree
ORDER BY (assessed_at, envelope_id);

CREATE TABLE IF NOT EXISTS openpulse.normalization_run (
    run_id String,
    envelope_id String,
    manufacturer String,
    status String,
    started_at DateTime64(3, 'UTC'),
    ended_at DateTime64(3, 'UTC'),
    records_in UInt32,
    records_out UInt32,
    rejected UInt32,
    notes String
) ENGINE = MergeTree
ORDER BY (started_at, manufacturer, run_id);

CREATE TABLE IF NOT EXISTS openpulse.failed_record_queue (
    failed_id String,
    envelope_json String,
    error_message String,
    failed_at DateTime64(3, 'UTC'),
    replay_status String,
    replayed_at Nullable(DateTime64(3, 'UTC'))
) ENGINE = MergeTree
ORDER BY (failed_at, replay_status);

CREATE TABLE IF NOT EXISTS openpulse.provenance_link (
    observation_id String,
    envelope_id String,
    payload_hash String,
    manufacturer String,
    mapping_version String,
    linked_at DateTime64(3, 'UTC')
) ENGINE = MergeTree
ORDER BY (observation_id, envelope_id);

CREATE TABLE IF NOT EXISTS openpulse.care_signal (
    care_signal_id String,
    subject_id String,
    signal_type String,
    severity String,
    generated_at DateTime64(3, 'UTC'),
    rationale_json String,
    source_feature_ids Array(String)
) ENGINE = MergeTree
ORDER BY (subject_id, generated_at);

CREATE TABLE IF NOT EXISTS openpulse.analytics_feature (
    feature_id String,
    subject_id String,
    feature_name String,
    feature_value Float64,
    feature_window String,
    generated_at DateTime64(3, 'UTC'),
    lineage_json String
) ENGINE = MergeTree
ORDER BY (subject_id, generated_at, feature_name);

CREATE TABLE IF NOT EXISTS openpulse.recommendation_event (
    recommendation_event_id String,
    subject_id String,
    recommendation_type String,
    recommendation_json String,
    status String,
    created_at DateTime64(3, 'UTC'),
    delivered_at Nullable(DateTime64(3, 'UTC'))
) ENGINE = MergeTree
ORDER BY (subject_id, created_at);

CREATE VIEW IF NOT EXISTS openpulse.gold_daily_subject_metrics AS
SELECT
    subject_id,
    toDate(event_time) AS metric_date,
    metric_code,
    avg(value) AS avg_value,
    min(value) AS min_value,
    max(value) AS max_value,
    count() AS sample_count,
    avg(quality_score) AS avg_quality
FROM openpulse.observation
WHERE value IS NOT NULL
GROUP BY subject_id, metric_date, metric_code;
