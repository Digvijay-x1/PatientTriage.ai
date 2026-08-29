"""
PatientTriage.ai - ML + Vital Safety Engine

Combines:
1. Random Forest ESI prediction
2. Age-aware VitalInterpreter
3. Pediatric AAP BP screening
4. Safety escalation
"""

from pathlib import Path

import joblib
import pandas as pd

from services.gemini_service import (
    GeminiExplanationService
)

# Supports either project layout:
#   PatientTriage/vital_interpreter.py
# or:
#   PatientTriage/services/vital_interpreter.py
try:
    from services.vital_interpreter import VitalInterpreter
except ModuleNotFoundError:
    from vital_interpreter import VitalInterpreter


# =========================================================
# MODEL PATH
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_PATH = (
    BASE_DIR
    / "ml"
    / "esi_integrated_model.joblib"
)

THRESHOLDS_PATH = (
    BASE_DIR
    / "ml"
    / "vitals_thresholds.json"
)


class TriageModel:

    def __init__(self):

        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"ML model not found: {MODEL_PATH}"
            )

        if not THRESHOLDS_PATH.exists():
            raise FileNotFoundError(
                f"Vital thresholds not found: {THRESHOLDS_PATH}"
            )

        self.model = joblib.load(MODEL_PATH)

        self.interpreter = VitalInterpreter(
            thresholds_path=str(THRESHOLDS_PATH)
        )

    # =====================================================
    # ASSESS PATIENT
    # =====================================================

    def assess_patient(self, patient):

        vitals = patient.get("vitals", {})
        age = patient.get("age")

        # -------------------------------------------------
        # Get raw sex/gender
        # -------------------------------------------------

        raw_sex = (
            patient.get("sex")
            or patient.get("gender")
        )

        if raw_sex is not None:
            normalized_sex = (
                str(raw_sex).strip().lower()
            )
        else:
            normalized_sex = None

        # -------------------------------------------------
        # VitalInterpreter requires "male"/"female"
        # -------------------------------------------------

        if normalized_sex in (
            "m", "male", "man", "boy"
        ):
            interpreter_sex = "male"

        elif normalized_sex in (
            "f", "female", "woman", "girl"
        ):
            interpreter_sex = "female"

        else:
            interpreter_sex = normalized_sex

        # -------------------------------------------------
        # ML model was trained with M/F
        # -------------------------------------------------

        if normalized_sex in (
            "m", "male", "man", "boy"
        ):
            gender = "M"

        elif normalized_sex in (
            "f", "female", "woman", "girl"
        ):
            gender = "F"

        else:
            gender = None

        # =================================================
        # 1. VITAL INTERPRETER
        # =================================================

        critical = 0
        urgent = 0
        vital_reasoning = []
        vital_results = []

        interpreter_vitals = {
            key: value
            for key, value in vitals.items()
            if value is not None
        }

        print("========== SEX DEBUG ==========")
        print("patient:", patient)
        print("raw sex:", repr(raw_sex))
        print("normalized sex:", repr(normalized_sex))
        print("interpreter sex:", repr(interpreter_sex))
        print("===============================")
        
        if interpreter_vitals:

            (
                critical,
                urgent,
                vital_reasoning,
                vital_results
            ) = self.interpreter.check_all_vitals(
                interpreter_vitals,
                age=age,
                sex=interpreter_sex
            )

        # =================================================
        # 2. PREPARE ML FEATURES
        # =================================================

        data = {
            "temperature": vitals.get("temperature"),
            "heartrate": vitals.get("hr"),
            "resprate": vitals.get("respiratory_rate"),
            "o2sat": vitals.get("spo2"),
            "sbp": vitals.get("bp_systolic"),
            "dbp": vitals.get("bp_diastolic"),
            "pain": vitals.get("pain"),
            "gender": gender,
            "chiefcomplaint": patient.get(
                "chief_complaint"
            ) or ""
        }

        X = pd.DataFrame([data])

        # =================================================
        # 3. ML PREDICTION
        # =================================================

        prediction = int(
            self.model.predict(X)[0]
        )

        probabilities = (
            self.model.predict_proba(X)[0]
        )

        classes = self.model.classes_

        best_index = probabilities.argmax()

        confidence = float(
            probabilities[best_index]
        )

        probability_breakdown = {
            f"esi_{int(cls)}": round(
                float(prob), 3
            )
            for cls, prob in zip(
                classes,
                probabilities
            )
        }

        # =================================================
        # 4. CONFIDENCE BAND
        # =================================================

        if confidence >= 0.80:
            confidence_band = "high"
        elif confidence >= 0.60:
            confidence_band = "medium"
        else:
            confidence_band = "low"

        # =================================================
        # 5. SAFETY ENGINE
        # =================================================

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

        clinical_review_required = (
            critical > 0
            or urgent > 0
            or confidence < 0.60
        )

        if critical > 0:
            safety_alerts.append(
                "Critical vital abnormality detected; "
                "clinical review required despite ML prediction."
            )

        # =================================================
        # 6. REASONING
        # =================================================

        reasoning = list(vital_reasoning)

        reasoning.append(
            f"ML model predicted ESI {prediction} "
            f"with {confidence:.1%} confidence."
        )

        if clinical_review_required:
            reasoning.append(
                "Safety engine recommends clinical review."
            )

        # =================================================
        # 7. SERIALIZE VITAL RESULTS
        # =================================================

        serialized_vitals = []

        for result in vital_results:

            if isinstance(result, dict):

                serialized_vitals.append(result)

            else:

                serialized_vitals.append({
                    "vital_name": result.vital_name,
                    "value": result.value,
                    "status": result.status,
                    "flag": result.flag,
                    "reasoning": result.reasoning
                })

        # =================================================
        # 8. FINAL RESULT
        # =================================================

        result = {
            "esi_level": prediction,
            "ml_esi": prediction,
            "confidence": round(confidence, 3),
            "confidence_band": confidence_band,
            "probabilities": probability_breakdown,
            "critical_flags": critical,
            "urgent_flags": urgent,
            "vital_results": serialized_vitals,
            "reasoning": reasoning,
            "safety_alerts": safety_alerts,
            "clinical_review_required":
                clinical_review_required,
            "auto_escalate_for_coordinator_review":
                clinical_review_required,
            "vital_details": data
        }

        # =================================================
        # GEMINI EXPLANATION
        # =================================================

        try:

            gemini_service = (
                GeminiExplanationService()
            )

            gemini_explanation = (
                gemini_service.explain_triage(
                    patient,
                    result
                )
            )

        except Exception as e:

            print(
                "Gemini explanation failed:",
                e
            )

            gemini_explanation = (
                "AI explanation unavailable. "
                "Please review the structured "
                "triage findings."
            )


        result["gemini_explanation"] = (
            gemini_explanation
        )

        return result
