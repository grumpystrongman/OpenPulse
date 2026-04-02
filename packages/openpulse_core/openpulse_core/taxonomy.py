from __future__ import annotations

METRIC_TAXONOMY: dict[str, dict[str, str]] = {
    "heart_rate": {"display": "Heart Rate", "canonical_unit": "beats/min"},
    "hrv_rmssd": {"display": "HRV RMSSD", "canonical_unit": "ms"},
    "sleep_duration": {"display": "Sleep Duration", "canonical_unit": "min"},
    "sleep_stage": {"display": "Sleep Stage", "canonical_unit": "stage"},
    "steps": {"display": "Steps", "canonical_unit": "count"},
    "energy_burned": {"display": "Energy Burned", "canonical_unit": "kcal"},
    "respiratory_rate": {"display": "Respiratory Rate", "canonical_unit": "breaths/min"},
    "spo2": {"display": "Pulse Oximetry", "canonical_unit": "%"},
    "skin_temperature": {"display": "Skin Temperature", "canonical_unit": "degC"},
    "stress_score": {"display": "Stress Score", "canonical_unit": "score"},
    "recovery_score": {"display": "Recovery Score", "canonical_unit": "score"},
    "blood_pressure_systolic": {"display": "Systolic Blood Pressure", "canonical_unit": "mmHg"},
    "blood_pressure_diastolic": {"display": "Diastolic Blood Pressure", "canonical_unit": "mmHg"},
    "body_weight": {"display": "Body Weight", "canonical_unit": "kg"},
    "body_fat_percent": {"display": "Body Fat Percent", "canonical_unit": "%"},
    "glucose": {"display": "Blood Glucose", "canonical_unit": "mg/dL"},
    "readiness_score": {"display": "Readiness Score", "canonical_unit": "score"},
    "strain_score": {"display": "Strain Score", "canonical_unit": "score"},
    "body_battery": {"display": "Body Battery", "canonical_unit": "score"},
    "menstrual_phase": {"display": "Menstrual Phase", "canonical_unit": "phase"},
}
