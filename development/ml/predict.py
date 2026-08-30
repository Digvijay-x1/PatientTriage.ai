"""PatientTriageAI integrated prediction helper.

Pipeline:
1. Validate/normalize the 12 CatBoost inputs.
2. Run the age-aware Vital Interpreter when age is supplied.
3. Run CatBoost and retain the complete five-class probability vector.
4. Apply explicit immediate-emergency and conservative safety escalation rules.
5. Return ML output, vital flags, completeness/reliability metadata, and safety reasoning.

The frozen CatBoost model and 12-input schema are intentionally unchanged.
Prototype only; not a clinical protocol or substitute for licensed clinician judgment.
"""
from pathlib import Path
import joblib
import numpy as np
import pandas as pd

from services.vital_interpreter import VitalInterpreter
from ml.history_context import evaluate_history



BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "catboost_esi_model_v2.joblib"
THRESHOLDS_PATH = BASE_DIR / "vitals_thresholds.json"

FEATURES = [
    "temperature", "heartrate", "resprate", "o2sat", "sbp", "dbp", "pain",
    "gender", "breathing", "responsiveness", "distress_level", "chiefcomplaint"
]
NUMERIC_FEATURES = ["temperature", "heartrate", "resprate", "o2sat", "sbp", "dbp", "pain"]
CATEGORICAL_FEATURES = ["gender", "breathing", "responsiveness", "distress_level", "chiefcomplaint"]

# The frozen model was trained on these exact categorical strings (verified
# against esi_training_data_5k.csv). Any other spelling/casing/vocabulary
# ("normal" vs "Normal", "laboured" vs "Labored", "low" vs "Mild") is an
# UNSEEN category to CatBoost and silently degrades the raw prediction --
# it does not raise an error, so this failure mode is easy to miss. This
# map normalizes known synonyms to the trained vocabulary before the model
# ever sees them. It is used only for the model's input; the safety-layer
# keyword checks below operate on the caller's original wording (widened
# separately) so no clinical nuance is lost by collapsing to 3-4 buckets.
_CATEGORICAL_SYNONYMS = {
    "gender": {
        "m": "M", "male": "M", "man": "M",
        "f": "F", "female": "F", "woman": "F",
    },
    "breathing": {
        "normal": "Normal",
        "mildly labored": "Mildly labored", "mildly laboured": "Mildly labored",
        "labored": "Labored", "laboured": "Labored",
        "severely labored": "Labored", "severely laboured": "Labored",
        "severe respiratory distress": "Labored",
        "not breathing": "Labored", "absent": "Labored", "no breathing": "Labored",
    },
    "responsiveness": {
        "alert": "Alert",
        "verbal": "Verbal", "responds to voice": "Verbal",
        "pain": "Pain", "responds to pain": "Pain",
        "unresponsive": "Unresponsive", "unconscious": "Unresponsive",
    },
    "distress_level": {
        "low": "Mild", "mild": "Mild",
        "moderate": "Moderate",
        "high": "Severe", "severe": "Severe",
    },
}


def _canonicalize_for_model(col, value):
    if _is_missing(value):
        return value
    key = str(value).strip().lower()
    synonyms = _CATEGORICAL_SYNONYMS.get(col)
    if synonyms and key in synonyms:
        return synonyms[key]
    return value

_MODEL = None
_INTERPRETER = None


def load_model():
    global _MODEL
    if _MODEL is None:
        _MODEL = joblib.load(MODEL_PATH)
    return _MODEL


def load_interpreter():
    global _INTERPRETER
    if _INTERPRETER is None:
        _INTERPRETER = VitalInterpreter(str(THRESHOLDS_PATH))
    return _INTERPRETER


def _is_missing(value):
    if value is None:
        return True
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


def _temperature_to_celsius(value):
    """Normalize temperature for the Vital Interpreter.

    The frozen model/training data are predominantly Fahrenheit (~96-100 F),
    while the Vital Interpreter configuration is Celsius. Inputs <=45 are
    treated as Celsius; higher values are treated as Fahrenheit. This keeps
    the existing 12-input interface while preventing a Celsius/Fahrenheit
    mismatch in the integrated path.
    """
    if _is_missing(value):
        return None
    value = float(value)
    if value <= 45.0:
        return value
    return (value - 32.0) * 5.0 / 9.0


def _temperature_for_model(value):
    """Convert Celsius-looking input to the frozen model's Fahrenheit scale."""
    if _is_missing(value):
        return np.nan
    value = float(value)
    if value <= 45.0:
        return value * 9.0 / 5.0 + 32.0
    return value


def prepare_patient(patient):
    if isinstance(patient, pd.DataFrame):
        df = patient.copy()
    elif isinstance(patient, dict):
        df = pd.DataFrame([patient])
    else:
        raise TypeError("patient must be a dict or pandas DataFrame")

    for col in FEATURES:
        if col not in df.columns:
            df[col] = np.nan
    df = df[FEATURES].copy()

    for col in NUMERIC_FEATURES:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # The frozen CatBoost model was trained with temperature values in
    # Fahrenheit. Preserve that model and normalize Celsius-looking inputs.
    df["temperature"] = df["temperature"].map(_temperature_for_model)

    for col in CATEGORICAL_FEATURES:
        if col in _CATEGORICAL_SYNONYMS:
            df[col] = df[col].map(lambda v, c=col: _canonicalize_for_model(c, v))
        df[col] = df[col].fillna("Unknown").astype(str)
        df.loc[df[col].str.strip().eq(""), col] = "Unknown"
    return df


def _missing_fields(X):
    missing = []
    for col in FEATURES:
        value = X.iloc[0][col]
        if pd.isna(value) or value == "Unknown":
            missing.append(col)
    return missing


def _data_reliability(completeness):
    if completeness >= 1.0:
        return "HIGH"
    if completeness >= 0.80:
        return "MODERATE"
    return "LOW"


def _run_vital_interpreter(patient):
    """Return age-aware vital interpretation without failing on missing data."""
    if _is_missing(patient.get("age")):
        return {
            "available": False, "age_group": None, "critical_count": 0,
            "urgent_count": 0, "critical_flags": [], "urgent_flags": [],
            "vitals": [], "reasoning": [], "error": "age not supplied"
        }

    try:
        age = int(patient["age"])
        interpreter = load_interpreter()
        sex = patient.get("gender") if not _is_missing(patient.get("gender")) else patient.get("sex")

        vitals = {}
        key_map = {
            "temperature": "temperature", "heartrate": "heart_rate",
            "resprate": "respiratory_rate", "o2sat": "spo2",
            "sbp": "systolic_bp", "dbp": "diastolic_bp", "pain": "pain"
        }

        for source, target in key_map.items():
            value = patient.get(source)
            if not _is_missing(value):
                if source == "temperature":
                    value = _temperature_to_celsius(value)
                vitals[target] = value

        critical = 0
        urgent = 0
        results = []
        reasoning = []

        # Pediatric BP is interpreted only when both values are present.
        if age < 13 and "systolic_bp" in vitals and "diastolic_bp" in vitals:
            try:
                bp = interpreter.interpret_pediatric_bp(
                    vitals["systolic_bp"], vitals["diastolic_bp"], age, sex=sex
                )
                results.append(bp)
                if bp["status"] == "critical":
                    critical += 1
                elif bp["status"] == "urgent":
                    urgent += 1
                if bp.get("flag"):
                    reasoning.append(bp.get("reasoning", ""))
            except ValueError as exc:
                reasoning.append(f"Pediatric BP interpretation unavailable: {exc}")

        for vital_name, value in vitals.items():
            if age < 13 and vital_name in {"systolic_bp", "diastolic_bp"}:
                continue
            try:
                result = interpreter.interpret_vital(
                    vital_name, value, age=age, sex=sex
                )
                results.append(result)
                if result.status == "critical":
                    critical += 1
                elif result.status == "urgent":
                    urgent += 1
                if result.flag:
                    reasoning.append(result.reasoning)
            except ValueError as exc:
                reasoning.append(f"{vital_name}: unavailable ({exc})")

        def serialize(x):
            if isinstance(x, dict):
                return x
            return {
                "vital_name": x.vital_name,
                "value": x.value,
                "status": x.status,
                "flag": x.flag,
                "reasoning": x.reasoning,
            }

        serialized = [serialize(x) for x in results]
        critical_flags = [x for x in serialized if x.get("status") == "critical"]
        urgent_flags = [x for x in serialized if x.get("status") == "urgent"]

        return {
            "available": True,
            "age": age,
            "age_group": interpreter.get_age_group(age),
            "critical_count": critical,
            "urgent_count": urgent,
            "critical_flags": critical_flags,
            "urgent_flags": urgent_flags,
            "vitals": serialized,
            "reasoning": reasoning,
            "error": None,
        }
    except Exception as exc:
        return {
            "available": False, "age_group": None, "critical_count": 0,
            "urgent_count": 0, "critical_flags": [], "urgent_flags": [],
            "vitals": [], "reasoning": [], "error": f"{type(exc).__name__}: {exc}"
        }



def _obvious_emergency(patient):
    """Identify only clear immediate life-threat patterns.

    Critical/urgent Vital Interpreter flags are safety signals. They are not,
    by themselves, ESI-1. ESI-1 requires an explicit immediate-life-threat
    pattern or a tightly defined collapse combination.
    """
    def norm(v):
        return "" if _is_missing(v) else str(v).strip().lower()

    complaint = norm(patient.get("chiefcomplaint"))
    responsiveness = norm(patient.get("responsiveness"))
    breathing = norm(patient.get("breathing"))
    distress = norm(patient.get("distress_level"))

    reasons = []

    if responsiveness in {"unresponsive", "unconscious"}:
        reasons.append("unresponsive/unconscious")

    if breathing in {"not breathing", "absent", "no breathing"}:
        reasons.append("not breathing")

    # Severe respiratory distress is an immediate threat when the clinical
    # presentation is objectively severe, rather than merely "labored".
    try:
        spo2 = float(patient.get("o2sat"))
    except (TypeError, ValueError):
        spo2 = None
    try:
        rr = float(patient.get("resprate"))
    except (TypeError, ValueError):
        rr = None

    if breathing in {"severely labored", "severely laboured", "severe respiratory distress"} and distress in {"severe", "high"}:
        if spo2 is None or spo2 <= 90 or rr is None or rr >= 50:
            reasons.append("severe respiratory distress with objective respiratory compromise")

    emergency_phrases = [
        "cardiac arrest", "no pulse", "pulseless",
        "respiratory arrest", "massive bleeding", "uncontrolled bleeding"
    ]
    if any(p in complaint for p in emergency_phrases):
        reasons.append("explicit life-threatening complaint")

    # Profound hypoxia plus concerning clinical context is an emergency.
    if spo2 is not None and spo2 <= 85 and (
        breathing in {"labored", "laboured", "severely labored", "severely laboured",
                       "severe respiratory distress", "not breathing", "absent", "no breathing"}
        or distress in {"high", "severe"}
    ):
        reasons.append("profound hypoxia with concerning clinical context")

    # Physiologic collapse safeguard.
    try:
        sbp = float(patient.get("sbp"))
    except (TypeError, ValueError):
        sbp = None
    if spo2 is not None and sbp is not None and spo2 <= 85 and sbp <= 90:
        reasons.append("critical oxygen saturation + low systolic BP")

    return bool(reasons), list(dict.fromkeys(reasons))


def _all_vitals_normal(vital):
    """True only when every supplied interpreted vital is normal."""
    supplied = vital.get("vitals", [])
    if not supplied:
        return False
    return all(x.get("status") == "normal" for x in supplied)


# Complaint terms that indicate a presentation which can still be
# genuinely concerning despite momentarily normal vitals (early sepsis,
# ACS, stroke, anaphylaxis, etc. can look deceptively stable). These
# BLOCK the low-acuity correction; by themselves they never raise acuity
# (that is _obvious_emergency's and the vital/history checks' job) -- they
# only stop this function from downgrading a complaint that deserves a
# clinician's eyes even though nothing measurable is abnormal yet.
_CONCERNING_COMPLAINT_TERMS = (
    "chest pain", "chest discomfort", "chest tightness", "chest pressure",
    "difficulty breathing", "shortness of breath", "can't breathe", "cannot breathe",
    "stroke", "weakness on one side", "facial droop", "slurred speech",
    "seizure", "overdose", "poisoning", "suicidal", "self harm", "self-harm",
    "allergic reaction", "anaphylaxis", "severe pain", "worst headache",
    "sudden severe", "uncontrolled bleeding", "coughing blood", "vomiting blood",
    "pregnant", "pregnancy", "miscarriage",
    "dizziness", "dizzy", "lightheaded", "light-headed", "light headed",
    "syncope", "presyncope", "vertigo", "fainting", "faint",
    "palpitation", "irregular heartbeat", "abdominal pain",
)

# A term on the blocklist above is only treated as genuinely concerning
# when it appears WITHOUT an explicit mitigating qualifier directly in
# front of it. "Dizziness" alone stays blocked (real ambiguity -- could be
# cardiac/stroke/orthostatic); "mild dizziness" is explicitly downgraded by
# the caller and should be allowed through to the low-acuity correction.
_MITIGATING_QUALIFIERS = ("mild", "minor", "slight")


def _is_concerning_complaint(complaint):
    for term in _CONCERNING_COMPLAINT_TERMS:
        idx = complaint.find(term)
        if idx == -1:
            continue
        prefix = complaint[:idx].strip()
        if not any(prefix.endswith(q) for q in _MITIGATING_QUALIFIERS):
            return True
    return False


_BP_VITAL_NAMES = {"systolic_bp", "diastolic_bp", "pediatric_blood_pressure"}


def _low_acuity_vitals_ok(vital):
    """True when every supplied vital is normal, OR there is at most one
    non-critical, non-blood-pressure urgent flag.

    Tolerating a single urgent flag avoids blocking the low-acuity
    correction on one borderline vital (e.g. a resting HR just outside a
    stricter pediatric band) that doesn't by itself reflect a genuinely
    concerning presentation. Blood-pressure flags are deliberately excluded
    from this tolerance: a pediatric BP screening flag specifically exists
    to catch early compensated shock, a materially higher-stakes category
    than a borderline heart rate or respiratory rate. Any critical flag, or
    2+ urgent flags of any kind, still blocks this correction entirely.
    """
    supplied = vital.get("vitals", [])
    if not supplied:
        return False
    if vital.get("critical_count", 0) > 0:
        return False
    urgent_flags = vital.get("urgent_flags", [])
    if len(urgent_flags) == 0:
        return True
    if len(urgent_flags) > 1:
        return False
    return urgent_flags[0].get("vital_name") not in _BP_VITAL_NAMES


def _low_acuity_profile(patient, vital, completeness):
    """Identify a low-acuity profile: complete data, normal-or-near-normal
    interpreted vitals, alert/normal breathing, low distress, low pain, and
    a complaint that isn't independently concerning.

    This function runs only after _obvious_emergency (explicit life-threat
    phrases + physiologic collapse combos) and the critical/urgent-vital-flag
    and relevant-history checks have already passed and found nothing. Given
    that, it doesn't need to re-derive "this is safe" from a narrow whitelist
    of exact benign phrases (which is brittle -- any new phrasing of a benign
    complaint falls through to the raw, ESI-2-biased model output). Instead
    it only needs to rule out complaints that are known to sometimes present
    with transiently normal vitals despite being genuinely serious.
    """
    if completeness < 1.0 or not vital.get("available"):
        return False

    if not _low_acuity_vitals_ok(vital):
        return False

    def norm(v):
        return "" if _is_missing(v) else str(v).strip().lower()

    if norm(patient.get("responsiveness")) not in {"alert"}:
        return False
    if norm(patient.get("breathing")) not in {"normal"}:
        return False
    if norm(patient.get("distress_level")) not in {"low", "mild"}:
        return False

    try:
        pain = float(patient.get("pain"))
    except (TypeError, ValueError):
        return False
    if pain > 3:
        return False

    complaint = norm(patient.get("chiefcomplaint"))
    if not complaint:
        return False

    if _is_concerning_complaint(complaint):
        return False

    return True


def _missing_data_adjustment(patient, vital, raw_pred, completeness):
    """Return a provisional acuity for materially incomplete presentations.

    With substantial missing physiologic data, the ML argmax is not treated as
    clinically reliable. Unless an emergency is independently established,
    ESI-3 is used as a provisional middle-acuity result and clinician review
    remains required. This avoids falsely reassuring ESI-4/5 decisions while
    also avoiding unjustified ESI-2 from missingness alone.
    """
    if completeness >= 0.75:
        return None, []
    reasons = [
        f"materially incomplete data ({completeness:.1%})",
        "provisional ESI-3 pending clinical assessment"
    ]
    return 3, reasons


def _safety_adjustment(patient, vital, raw_pred, completeness, history):
    """Apply immediate-emergency, physiologic-safety, history, low-acuity
    and missing-data rules."""
    emergency, emergency_reasons = _obvious_emergency(patient)

    if emergency:
        return 1, True, emergency_reasons, "IMMEDIATE_EMERGENCY"

    safety_reasons = []
    dangerous_non_emergency = False

    if raw_pred == 1:
        safety_reasons.append("non-emergency ESI-1 guard")

    critical_non_pain = [
        f for f in vital.get("critical_flags", [])
        if f.get("vital_name") not in {"pain"}
    ]

    # Multiple/any critical physiologic abnormalities should prevent an ML
    # ESI-3/4/5 from masking a clearly high-acuity presentation. This is an
    # acuity ceiling (maximum numeric ESI), not a minimum.
    if len(critical_non_pain) >= 2:
        dangerous_non_emergency = True
        safety_reasons.append(
            f"{len(critical_non_pain)} critical physiologic vital flags"
        )
    elif len(critical_non_pain) == 1:
        dangerous_non_emergency = True
        safety_reasons.append("critical physiologic vital flag")

    if vital.get("urgent_count", 0) >= 3:
        dangerous_non_emergency = True
        safety_reasons.append("cluster of >=3 urgent vital flags")

    # Relevant prior-history risk (e.g. cardiac history + chest pain) is
    # treated the same way as a critical vital flag: it can raise the
    # acuity floor, never lower it, and never on its own to ESI-1. Absent
    # `has_prior_record`/history_* fields, history.relevant_flags is
    # always empty, so this is a no-op for any caller not opting in.
    if history is not None and history.has_relevant_risk:
        dangerous_non_emergency = True
        for flag in history.relevant_flags:
            safety_reasons.append(f"relevant history: {flag.reasoning}")

    # Missingness is handled before low-acuity logic. Never let incomplete
    # data turn into an apparently reassuring ESI-4/5.
    missing_esi, missing_reasons = _missing_data_adjustment(
        patient, vital, raw_pred, completeness
    )
    if missing_esi is not None:
        # If an independent dangerous-vital signal exists, retain ESI-2;
        # otherwise use provisional ESI-3 and force clinician review.
        if dangerous_non_emergency or raw_pred == 1:
            adjusted = 2
        else:
            adjusted = 3
        return adjusted, False, safety_reasons + missing_reasons, "INCOMPLETE_DATA_PROVISIONAL"

    # A dangerous physiologic presentation cannot remain ESI-3/4/5 merely
    # because the ML argmax is less acute. It is still NOT ESI-1 unless the
    # immediate-emergency function above fired.
    if dangerous_non_emergency:
        adjusted = 2
        if raw_pred == 1:
            return 2, False, safety_reasons, "SAFETY_ESCALATION"
        if raw_pred != 2:
            return adjusted, False, safety_reasons, "SAFETY_ESCALATION"
        return 2, False, safety_reasons, "SAFETY_SIGNAL_NO_CHANGE"

    # Narrow low-acuity correction for complete, objectively normal profiles.
    # This MUST run before the raw_pred==1 guard below: the raw model's
    # ESI-1 over-triggering on harmless complaints (mild dizziness, minor
    # nausea) is exactly the same bias already corrected for ESI-2 -- a
    # flat "raw_pred==1 -> ESI-2" rule would silently re-introduce that
    # bias for the ESI-1 case and block this correction from ever running.
    if _low_acuity_profile(patient, vital, completeness):
        complaint = str(patient.get("chiefcomplaint") or "").strip().lower()
        if any(term in complaint for term in ("medication refill", "prescription refill", "routine refill")):
            low_esi = 5
        else:
            low_esi = 4
        return low_esi, False, ["complete low-acuity profile with normal vitals"], "LOW_ACUITY_PROFILE"

    if raw_pred == 1:
        return 2, False, safety_reasons, "SAFETY_ESCALATION"

    return raw_pred, False, [], "ML_DECISION"

def predict_patient(patient, audit=True):
    model = load_model()
    X = prepare_patient(patient)
    missing = _missing_fields(X)
    completeness = float(1.0 - len(missing) / len(FEATURES))
    reliability = _data_reliability(completeness)

    vital = _run_vital_interpreter(patient)
    history = evaluate_history(patient)

    # Always run CatBoost first so ML prediction/probabilities remain visible
    # even when the safety engine ultimately forces ESI-1.
    raw_pred = int(np.asarray(model.predict(X)).reshape(-1)[0])
    probs = np.asarray(model.predict_proba(X))[0]
    classes = np.asarray(model.classes_).astype(int)
    confidence = float(np.max(probs))

    final_esi, emergency, decision_reasons, safety_decision = _safety_adjustment(
        patient, vital, raw_pred, completeness, history
    )

    # Facility context is computed on the final ESI, after the safety
    # engine, and never feeds back into acuity -- it only decides whether
    # a transfer should be recommended.

    clinician_review_required = reliability == "LOW"

    result = {
        "acuity": int(final_esi),
        "confidence": None if emergency else confidence,
        "confidence_display": not emergency,
        "probabilities": {str(int(c)): float(p) for c, p in zip(classes, probs)},
        "missing_fields": missing,
        "data_completeness": completeness,
        "decision_reliability": reliability,
        "clinician_review_required": clinician_review_required,
        "emergency_override": emergency,
        "emergency_reasons": decision_reasons if emergency else [],
        "safety_reasons": [] if emergency else decision_reasons,
        "safety_decision": safety_decision,
        "ml_raw_acuity": raw_pred,
        "non_emergency_esi1_guard": bool(raw_pred == 1 and not emergency),
        "vital_interpreter": vital,
        "history_context": {
            "has_prior_record": history.has_prior_record,
            "conditions_present": history.conditions_present,
            "relevant_risk": history.has_relevant_risk,
        },
    }


    return result


if __name__ == "__main__":
    print("=" * 70)
    print("PATIENTTRIAGE.AI - INTEGRATED SMOKE TEST")
    print("=" * 70)
    result = predict_patient({"age": 35, **{f: None for f in FEATURES}})
    print("SUCCESS")
    print("Final ESI:", result["acuity"])
    print("ML raw ESI:", result["ml_raw_acuity"])
    print("Probabilities:", result["probabilities"])
    print("Reliability:", result["decision_reliability"])
    print("Clinician review required:", result["clinician_review_required"])
    print("Vital interpreter:", result["vital_interpreter"]["error"] or "OK")
