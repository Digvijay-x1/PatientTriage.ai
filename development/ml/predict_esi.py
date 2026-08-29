"""
PatientTriage.ai - Integrated ESI Prediction

Combines:
1. Machine Learning ESI prediction
2. Age-aware VitalInterpreter
3. Safety Engine

Important model/training detail:
The current MIMIC-IV-ED demo training CSV has no age column. Therefore the
saved ML model uses a fixed adult reference age when generating its derived
ML flags. The live VitalInterpreter still uses the patient's actual age for
safety interpretation, including pediatric BP screening.
"""

from pathlib import Path

import joblib
import pandas as pd

from development.services.vital_interpreter import VitalInterpreter


MODEL_PATH = Path("esi_integrated_model.joblib")


# ============================================================
# HELPERS
# ============================================================

def normalize_sex(value):
    """Normalize sex/gender input to male/female/unknown."""

    if value is None:
        return None

    value = str(value).strip().lower()

    if value in {"m", "male", "man", "boy"}:
        return "male"

    if value in {"f", "female", "woman", "girl"}:
        return "female"

    raise ValueError(
        "sex/gender must be male/female (or M/F)."
    )


def ml_gender_code(sex):
    """Convert canonical sex to the training model's M/F vocabulary."""

    if sex == "male":
        return "M"

    if sex == "female":
        return "F"

    return "UNKNOWN"


def get_vital_field(vital, field):
    """Read a field from either a VitalResult or dictionary result."""

    if isinstance(vital, dict):
        return vital.get(field)

    return getattr(vital, field, None)


def get_model_feature_columns(model):
    """Return the raw columns the saved model expects."""

    if hasattr(model, "feature_names_in_"):
        return list(model.feature_names_in_)

    if hasattr(model, "training_feature_columns"):
        return list(model.training_feature_columns)

    raise ValueError(
        "Saved model does not expose its expected feature columns."
    )


def get_model_flag_age(model):
    """
    Return the age used to create interpreter-derived ML flags during training.

    New models store this explicitly. The fallback preserves compatibility
    with older integrated models that used age=30.
    """

    return int(
        getattr(
            model,
            "ml_flag_reference_age",
            30
        )
    )


# ============================================================
# MAIN PREDICTION FUNCTION
# ============================================================

def predict_esi(
    vitals,
    age,
    gender=None,
    chiefcomplaint="",
    sex=None
):

    # ========================================================
    # 0. NORMALIZE SEX / GENDER
    # ========================================================

    if sex is None:
        sex = gender

    sex = normalize_sex(sex)

    # ========================================================
    # 1. LOAD MODEL
    # ========================================================

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            "esi_integrated_model.joblib not found."
        )

    model = joblib.load(MODEL_PATH)

    # ========================================================
    # 2. RUN LIVE, AGE-AWARE VITAL INTERPRETER
    # ========================================================

    interpreter = VitalInterpreter()

    critical, urgent, reasoning, results = (
        interpreter.check_all_vitals(
            vitals,
            age,
            sex=sex
        )
    )

    # ========================================================
    # 3. PREPARE ML FEATURES
    # ========================================================

    # The ML model uses measured vitals + gender + chief complaint only.
    # Age-specific threshold interpretation remains in the independent
    # VitalInterpreter/Safety Engine.
    data = {
        "temperature": vitals.get("temperature"),
        "heartrate": vitals.get("heart_rate"),
        "resprate": vitals.get("respiratory_rate"),
        "o2sat": vitals.get("spo2"),
        "sbp": vitals.get("systolic_bp"),
        "dbp": vitals.get("diastolic_bp"),
        "pain": vitals.get("pain"),
        "gender": ml_gender_code(sex),
        "chiefcomplaint": "" if chiefcomplaint is None else str(chiefcomplaint)
    }

    # ========================================================
    # 5. CREATE DATAFRAME
    # ========================================================

    X = pd.DataFrame([data])

    expected_features = get_model_feature_columns(model)
    current_features = list(X.columns)

    missing_features = [
        feature
        for feature in expected_features
        if feature not in current_features
    ]

    extra_features = [
        feature
        for feature in current_features
        if feature not in expected_features
    ]

    if missing_features:
        raise ValueError(
            "Model input is missing required features: "
            + ", ".join(missing_features)
        )

    if extra_features:
        X = X.drop(columns=extra_features)

    # Exact training order.
    X = X[expected_features]

    # ========================================================
    # 6. DEBUG / MODEL INPUT
    # ========================================================

    print("\nMODEL INPUT FEATURES:")
    print(list(X.columns))

    print("LIVE PATIENT AGE:", age)

    # ========================================================
    # 7. ML PREDICTION
    # ========================================================

    prediction = model.predict(X)[0]
    probabilities = model.predict_proba(X)[0]

    try:
        classes = model.named_steps["classifier"].classes_
    except AttributeError:
        classes = model.classes_

    best_index = probabilities.argmax()
    confidence = float(probabilities[best_index])

    probability_dict = {
        int(class_label): round(float(probability), 3)
        for class_label, probability in zip(classes, probabilities)
    }

    # ========================================================
    # 8. SAFETY ENGINE
    # ========================================================

    safety_alerts = []

    if critical > 0:
        safety_alerts.append(
            f"{critical} critical vital "
            f"abnormality/abnormalities detected."
        )

    if urgent > 0:
        safety_alerts.append(
            f"{urgent} urgent vital "
            f"abnormality/abnormalities detected."
        )

    if confidence < 0.60:
        safety_alerts.append(
            "ML confidence is below 60%."
        )

    # The current demo model was trained without age, so explicitly warn when
    # a pediatric patient is being evaluated by the ML model.
    if age < 13:
        safety_alerts.append(
            "ML model was trained without patient age; "
            "pediatric interpretation is handled separately by the "
            "age-aware VitalInterpreter."
        )

    # ========================================================
    # 9. SAFETY OVERRIDE / ESCALATION
    # ========================================================

    final_esi = int(prediction)

    if critical >= 1 and final_esi > 1:
        safety_alerts.append(
            "Critical vital abnormality detected; "
            "clinical review required despite ML prediction."
        )

    # ========================================================
    # 10. RETURN RESULT
    # ========================================================

    return {
        "esi": final_esi,
        "ml_esi": int(prediction),
        "confidence": round(confidence, 3),
        "probabilities": probability_dict,
        "critical_flags": critical,
        "urgent_flags": urgent,
        "vital_results": results,
        "reasoning": reasoning,
        "safety_alerts": safety_alerts
    }


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("PATIENTTRIAGE.AI")
    print("INTEGRATED ESI TEST")
    print("=" * 60)

    patient_vitals = {
        "spo2": 88,
        "heart_rate": 115,
        "respiratory_rate": 32,
        "systolic_bp": 155,
        "diastolic_bp": 90,
        "temperature": 37.2,
        "pain": 7
    }

    result = predict_esi(
        vitals=patient_vitals,
        age=52,
        sex="male",
        chiefcomplaint="difficulty breathing"
    )

    print("\nML PREDICTION")
    print("-" * 40)
    print("ML ESI:", result["ml_esi"])
    print("ML Confidence:", result["confidence"])
    print("Probabilities:", result["probabilities"])
    print("Final ESI:", result["esi"])

    print("\nVITAL INTERPRETER")
    print("-" * 40)

    for vital in result["vital_results"]:

        vital_name = get_vital_field(vital, "vital_name")
        status = get_vital_field(vital, "status")

        if vital_name == "pediatric_blood_pressure":
            print(
                f"{vital_name}: "
                f"SBP={get_vital_field(vital, 'systolic_bp')}, "
                f"DBP={get_vital_field(vital, 'diastolic_bp')} -> "
                f"{status.upper()}"
            )
        else:
            print(
                f"{vital_name}: "
                f"{get_vital_field(vital, 'value')} -> "
                f"{status.upper()}"
            )

    print("\nCritical flags:", result["critical_flags"])
    print("Urgent flags:", result["urgent_flags"])

    print("\nREASONING")
    print("-" * 40)

    for reason in result["reasoning"]:
        print("-", reason)

    print("\nSAFETY ENGINE")
    print("-" * 40)

    for alert in result["safety_alerts"]:
        print("WARNING:", alert)

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
