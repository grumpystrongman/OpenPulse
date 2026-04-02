-- Gold marts and feature tables
CREATE VIEW IF NOT EXISTS openpulse.gold_subject_daily_recovery AS
SELECT
  subject_id,
  toDate(event_time) AS metric_date,
  avgIf(value, metric_code = 'recovery_score') AS avg_recovery,
  avgIf(value, metric_code = 'readiness_score') AS avg_readiness,
  avgIf(value, metric_code = 'stress_score') AS avg_stress
FROM openpulse.observation
GROUP BY subject_id, metric_date;

CREATE VIEW IF NOT EXISTS openpulse.gold_subject_daily_cardio AS
SELECT
  subject_id,
  toDate(event_time) AS metric_date,
  avgIf(value, metric_code = 'heart_rate') AS avg_hr,
  avgIf(value, metric_code = 'hrv_rmssd') AS avg_hrv,
  avg(quality_score) AS avg_quality
FROM openpulse.observation
GROUP BY subject_id, metric_date;
