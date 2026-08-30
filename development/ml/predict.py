"""PatientTriage.ai - fixed drop-in prediction helper.

Key fixes:
1. Validate numeric inputs instead of silently accepting impossible values.
2. Normalize categorical values consistently.
3. Use the CatBoost model's normal argmax for NON-EMERGENCY cases.
   The previous safety-biased expected-cost rule over-predicted ESI-2.
4. Preserve hard emergency overrides for obvious ESI-1 presentations.
5. Add conservative low-acuity routing for clearly stable, minor/no-resource cases.
6. Preserve the output fields used by the existing test suite.

This is a research/prototype triage helper, not a clinical device.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional

import numpy as np
import pandas as pd
import joblib


BASE_DIR = Path(__file__).resolve().parent
MODEL_CANDIDATES = [
    BASE_DIR / "catboost_esi_model_v3.joblib",
    BASE_DIR / "catboost_safety_biased_model.joblib",
    BASE_DIR / "catboost_robust_5k.joblib",
]

FEATURES = [
    "temperature", "heartrate", "resprate", "o2sat", "sbp", "dbp", "pain",
    "gender", "breathing", "responsiveness", "distress_level", "chiefcomplaint",
]

NUMERIC_FEATURES = [
    "temperature", "heartrate", "resprate", "o2sat", "sbp", "dbp", "pain"
]
CATEGORICAL_FEATURES = [
    "gender", "breathing", "responsiveness", "distress_level", "chiefcomplaint"
]

_ALLOWED = {
    "gender": {
        "m": "M", "male": "M", "f": "F", "female": "F", "unknown": "Unknown",
        "": "Unknown", "none": "Unknown",
    },
    "breathing": {
        "normal": "normal",
        "labored": "labored",
        "mildly labored": "mildly labored",
        "severely labored": "severely labored",
        "absent": "absent",
        "unknown": "Unknown", "": "Unknown", "none": "Unknown",
    },
    "responsiveness": {
        "alert": "alert",
        "verbal": "verbal",
        "drowsy": "drowsy",
        "confused": "confused",
        "unresponsive": "unresponsive",
        "pain": "pain",
        "unknown": "Unknown", "": "Unknown", "none": "Unknown",
    },
    "distress_level": {
        "none": "none",
        "low": "low",
        "mild": "mild",
        "moderate": "moderate",
        "high": "high",
        "severe": "severe",
        "unknown": "Unknown", "": "Unknown", "none": "Unknown",
    },
}

# Complaints whose stable presentation is normally very low-acuity in this
# prototype. These are deliberately narrow; unknown complaints do not get a
# forced ESI-5.
NO_RESOURCE_COMPLAINTS = (
    "medication refill",
    "prescription request",
    "suture removal",
    "minor rash",
    "mild runny nose",
    "simple request",
)

ONE_RESOURCE_COMPLAINTS = (
    "minor laceration",
    "mild headache",
    "burning urination",
    "urinary symptoms",
    "earache",
    "rash",
    "dental pain",
    "minor injury",
)

HIGH_RISK_COMPLAINTS = (
    "chest pain",
    "chest discomfort",
    "severe bleeding",
    "gi bleed",
    "altered mental status",
    "stroke",
    "sepsis",
    "major trauma",
    "overdose",
)

LIFE_THREATENING_TERMS = (
    "cardiac arrest",
    "unresponsive",
    "unconscious",
    "not breathing",
    "status epilepticus",
    "severe altered mental status",
)


def _load_model():
    for path in MODEL_CANDIDATES:
        if path.exists():
            obj = joblib.load(path)
            if isinstance(obj, dict) and "model" in obj:
                return obj["model"], obj
            return obj, {}
    raise FileNotFoundError(
        "No CatBoost model found. Put catboost_safety_biased_model.joblib or "
        "catboost_robust_5k.joblib beside predict.py."
    )


MODEL, MODEL_META = _load_model()


def _normalise_text(v: Any) -> Optional[str]:
    if v is None:
        return None
    if isinstance(v, float) and math.isnan(v):
        return None
    s = str(v).strip()
    return s if s else None


def _normalise_categories(patient: Mapping[str, Any]) -> Dict[str, Any]:
    out = dict(patient)
    for field, mapping in _ALLOWED.items():
        value = _normalise_text(out.get(field))
        if value is None:
            out[field] = "Unknown"
            continue
        key = value.lower()
        if field in mapping:
            if key not in mapping:
                raise ValueError(f"Invalid {field}: {value!r}")
            out[field] = mapping[key]
        else:
            out[field] = value
    # Preserve complaint capitalization/content while normalising whitespace.
    complaint = _normalise_text(out.get("chiefcomplaint"))
    out["chiefcomplaint"] = complaint if complaint is not None else "Unknown"
    return out


def _validate_patient(patient: Mapping[str, Any]) -> Dict[str, Any]:
    if not isinstance(patient, Mapping):
        raise TypeError("patient must be a dict or pandas DataFrame")

    out = dict(patient)
    for field in FEATURES:
        out.setdefault(field, None)

    for field in NUMERIC_FEATURES:
        value = out[field]
        if value is None or (isinstance(value, float) and math.isnan(value)):
            continue
        if isinstance(value, bool) or not isinstance(value, (int, float, np.number)):
            raise TypeError(f"{field} must be numeric or None")
        value = float(value)
        if not math.isfinite(value):
            raise ValueError(f"{field} must be finite")
        out[field] = value

    # Plausibility checks. These are input-validation bounds, not diagnostic thresholds.
    bounds = {
        "temperature": (20.0, 45.0),
        "heartrate": (0.0, 260.0),
        "resprate": (0.0, 160.0),
        "o2sat": (0.0, 100.0),
        "sbp": (0.0, 320.0),
        "dbp": (0.0, 220.0),
        "pain": (0.0, 10.0),
    }
    for field, (lo, hi) in bounds.items():
        value = out[field]
        if value is not None and not (lo <= float(value) <= hi):
            raise ValueError(f"{field} outside accepted input range [{lo}, {hi}]")

    return _normalise_categories(out)


def _prepare_df(patient: Mapping[str, Any]) -> pd.DataFrame:
    p = _validate_patient(patient)
    row = {f: p[f] for f in FEATURES}
    return pd.DataFrame([row], columns=FEATURES)


def _missing_fields(patient: Mapping[str, Any]) -> List[str]:
    return [f for f in FEATURES if patient.get(f) is None or patient.get(f) == "Unknown"]


def _data_completeness(patient: Mapping[str, Any]) -> float:
    missing = len(_missing_fields(patient))
    return max(0.0, 1.0 - missing / len(FEATURES))


def _complaint(patient: Mapping[str, Any]) -> str:
    return str(patient.get("chiefcomplaint") or "").strip().lower()


def _has_any(text: str, phrases: Iterable[str]) -> bool:
    return any(p in text for p in phrases)


def _objective_emergency(patient: Mapping[str, Any]) -> List[str]:
    reasons: List[str] = []
    complaint = _complaint(patient)
    resp = str(patient.get("responsiveness", "")).lower()
    breathing = str(patient.get("breathing", "")).lower()
    distress = str(patient.get("distress_level", "")).lower()

    if resp in {"unresponsive", "unconscious"} or _has_any(complaint, ("unresponsive", "unconscious")):
        reasons.append("unresponsive/unconscious")
    if breathing == "absent" or float(patient.get("resprate") or 0) == 0 or _has_any(complaint, ("cardiac arrest", "not breathing")):
        reasons.append("not breathing")
    if patient.get("o2sat") is not None and float(patient["o2sat"]) < 90:
        reasons.append("profound hypoxia with concerning clinical context")
    if patient.get("sbp") is not None and float(patient["sbp"]) < 80:
        reasons.append("profound hypotension")
    if breathing in {"severely labored", "severe difficulty"} and (
        (patient.get("resprate") is not None and float(patient["resprate"]) >= 30)
        or (patient.get("o2sat") is not None and float(patient["o2sat"]) < 90)
    ):
        reasons.append("severe respiratory distress with objective respiratory compromise")
    if _has_any(complaint, LIFE_THREATENING_TERMS):
        reasons.append("explicit life-threatening complaint")
    if distress == "severe" and (
        (patient.get("o2sat") is not None and float(patient["o2sat"]) < 85)
        or breathing == "absent"
    ):
        reasons.append("severe distress with objective compromise")
    return list(dict.fromkeys(reasons))


def _high_risk_non_emergency(patient: Mapping[str, Any]) -> List[str]:
    reasons: List[str] = []
    complaint = _complaint(patient)
    if _has_any(complaint, HIGH_RISK_COMPLAINTS):
        reasons.append("high-risk complaint")
    if str(patient.get("responsiveness", "")).lower() in {"confused", "drowsy", "pain"}:
        reasons.append("altered responsiveness")
    if str(patient.get("distress_level", "")).lower() in {"high", "severe"}:
        reasons.append("high clinical distress")
    if patient.get("o2sat") is not None and float(patient["o2sat"]) < 94:
        reasons.append("low oxygen saturation")
    if patient.get("sbp") is not None and float(patient["sbp"]) < 90:
        reasons.append("low systolic blood pressure")
    if patient.get("heartrate") is not None and float(patient["heartrate"]) >= 130:
        reasons.append("marked tachycardia")
    if patient.get("resprate") is not None and float(patient["resprate"]) >= 30:
        reasons.append("marked tachypnea")
    return list(dict.fromkeys(reasons))


def _stable_low_acuity(patient: Mapping[str, Any]) -> bool:
    complaint = _complaint(patient)
    resp = str(patient.get("responsiveness", "")).lower()
    breathing = str(patient.get("breathing", "")).lower()
    distress = str(patient.get("distress_level", "")).lower()

    if resp not in {"alert", "verbal"}:
        return False
    if breathing not in {"normal"}:
        return False
    if distress not in {"none", "low"}:
        return False

    vals = {k: patient.get(k) for k in ("o2sat", "sbp", "dbp", "heartrate", "resprate")}
    if any(v is None for v in vals.values()):
        return False
    if not (95 <= vals["o2sat"] <= 100):
        return False
    if not (90 <= vals["sbp"] <= 180):
        return False
    if not (50 <= vals["heartrate"] <= 110):
        return False
    if not (10 <= vals["resprate"] <= 22):
        return False
    if patient.get("pain") is not None and float(patient["pain"]) > 4:
        return False
    return True


def _low_acuity_override(patient: Mapping[str, Any], raw_esi: int) -> Optional[int]:
    if not _stable_low_acuity(patient):
        return None
    complaint = _complaint(patient)
    if any(p in complaint for p in NO_RESOURCE_COMPLAINTS):
        return 5
    if any(p in complaint for p in ONE_RESOURCE_COMPLAINTS):
        return 4
    # Don't downgrade an unknown/still-concerning complaint merely because the
    # model predicts a middle class.
    if raw_esi in {4, 5}:
        return raw_esi
    return None


def _confidence(probs: Dict[str, float], missing: List[str], override: bool) -> Optional[float]:
    if override:
        return None
    top = max(probs.values()) if probs else 0.0
    # Reduce displayed confidence with missingness, but keep it bounded.
    factor = max(0.0, 1.0 - 0.35 * len(missing) / len(FEATURES))
    return float(top * factor)


def predict_patient(patient: Any) -> Dict[str, Any]:
    # DataFrame support for backward compatibility.
    if isinstance(patient, pd.DataFrame):
        if len(patient) != 1:
            raise ValueError("predict_patient expects exactly one patient row")
        patient = patient.iloc[0].to_dict()

    p = _validate_patient(patient)
    missing = [f for f in FEATURES if p.get(f) is None or p.get(f) == "Unknown"]
    completeness = max(0.0, 1.0 - len(missing) / len(FEATURES))

    X = _prepare_df(p)
    raw_probs_arr = MODEL.predict_proba(X)[0]
    classes = [int(x) for x in MODEL.classes_]
    raw_probs = {str(cls): float(prob) for cls, prob in zip(classes, raw_probs_arr)}
    raw_esi = int(classes[int(np.argmax(raw_probs_arr))])

    emergency_reasons = _objective_emergency(p)
    high_risk_reasons = _high_risk_non_emergency(p)

    if emergency_reasons:
        acuity = 1
        confidence = None
        decision_reliability = "HIGH"
        clinician_review_required = False
        emergency_override = True
        safety_decision = "IMMEDIATE_EMERGENCY"
        safety_reasons: List[str] = []
    else:
        # IMPORTANT FIX: non-emergency prediction uses the model's normal argmax,
        # not the under-triage-penalized expected-cost rule that collapsed cases
        # toward ESI-2.
        acuity = raw_esi
        low_override = _low_acuity_override(p, raw_esi)
        if low_override is not None and raw_esi in {2, 3}:
            acuity = low_override

        confidence = _confidence(raw_probs, missing, override=False)
        if completeness >= 0.95:
            decision_reliability = "HIGH"
        elif completeness >= 0.65:
            decision_reliability = "MODERATE"
        else:
            decision_reliability = "LOW"
        clinician_review_required = completeness < 0.65
        emergency_override = False
        safety_reasons = []
        safety_decision = "ML_DECISION"

        unknown_categorical = [f for f in ("gender", "breathing", "responsiveness", "distress_level", "chiefcomplaint") if p.get(f) == "Unknown"]
        if unknown_categorical:
            clinician_review_required = True
            safety_reasons.append("unknown/missing categorical data: " + ", ".join(unknown_categorical))
            safety_decision = "SAFETY_ESCALATION"

        # Missing-data safety review. Do not force an ESI-1 merely because a
        # probability is high when there is no objective emergency evidence.
        if completeness < 0.65:
            clinician_review_required = True
            safety_reasons.append("materially incomplete patient data")
            safety_decision = "SAFETY_ESCALATION"

        if high_risk_reasons and acuity > 2:
            acuity = 2
            safety_reasons.append("high-risk presentation guard")
            safety_decision = "SAFETY_ESCALATION"

        # For raw ESI-1 without objective life-threat evidence, do not expose it
        # as an ESI-1 decision; route to ESI-2 with a safety reason instead.
        if raw_esi == 1 and acuity == 1 and not emergency_reasons:
            acuity = 2
            safety_reasons.append("non-emergency ESI-1 guard")
            safety_decision = "SAFETY_ESCALATION"

    return {
        "acuity": int(acuity),
        "confidence": confidence,
        "confidence_display": confidence is not None,
        "probabilities": raw_probs,
        "missing_fields": missing,
        "data_completeness": float(completeness),
        "decision_reliability": decision_reliability,
        "clinician_review_required": bool(clinician_review_required),
        "emergency_override": bool(emergency_override),
        "emergency_reasons": emergency_reasons,
        "safety_reasons": safety_reasons,
        "safety_decision": safety_decision,
        "ml_raw_acuity": raw_esi,
        "non_emergency_esi1_guard": (raw_esi == 1 and not emergency_reasons),
    }


__all__ = ["predict_patient", "FEATURES"]
