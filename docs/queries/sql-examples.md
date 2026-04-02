# Query Examples

## 1) Longitudinal subject timeline
```sql
SELECT event_time, metric_code, value, unit, manufacturer
FROM openpulse.observation
WHERE subject_id = 'sub-00001'
ORDER BY event_time;
```

## 2) 12-month glucose trend by week
```sql
SELECT toStartOfWeek(event_time) AS week_start, avg(value) AS avg_glucose
FROM openpulse.observation
WHERE metric_code = 'glucose' AND event_time >= now() - INTERVAL 12 MONTH
GROUP BY week_start
ORDER BY week_start;
```

## 3) Device reliability: missing cadence windows
```sql
SELECT manufacturer, count() AS missing_windows
FROM (
  SELECT manufacturer, subject_id, toStartOfHour(event_time) AS hour_bucket, count() AS n
  FROM openpulse.observation
  GROUP BY manufacturer, subject_id, hour_bucket
  HAVING n < 3
)
GROUP BY manufacturer
ORDER BY missing_windows DESC;
```

## 4) Data quality scorecards
```sql
SELECT metric_code, avg(score) AS avg_quality
FROM openpulse.quality_assessment qa
JOIN openpulse.observation o ON qa.observation_id = o.observation_id
GROUP BY metric_code
ORDER BY avg_quality DESC;
```
