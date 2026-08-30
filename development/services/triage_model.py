import sys
from pathlib import Path

# =========================================================
# V2 ML PIPELINE
# =========================================================

ML_DIR = (
    Path(__file__).resolve().parent.parent
    / "ml"
)

if str(ML_DIR) not in sys.path:
    sys.path.insert(0, str(ML_DIR))

from ml.predict import predict_patient


# =========================================================
# CONFIDENCE BAND
# =========================================================

def _confidence_band(confidence):
    if confidence is None:
        return "emergency_override"

    if confidence >= 0.80:
        return "high"

    if confidence >= 0.60:
        return "medium"

    return "low"


# =========================================================
# TRIAGE MODEL
# =========================================================

class TriageModel:

    def __init__(self):
        """
        V2 prediction pipeline:

            CatBoost
                ↓
            Vital Interpreter
                ↓
            Safety Engine
                ↓
            Final ESI
        """

        pass

    # =====================================================
    # ASSESS PATIENT
    # =====================================================

    def assess_patient(self, patient):

        # -------------------------------------------------
        # Patient data
        # -------------------------------------------------

        vitals = patient.get(
            "vitals",
            {}
        )

        # -------------------------------------------------
        # Normalize gender
        # -------------------------------------------------

        raw_sex = (
            patient.get("sex")
            or patient.get("gender")
        )

        if raw_sex is not None:

            normalized_sex = (
                str(raw_sex)
                .strip()
                .lower()
            )

        else:

            normalized_sex = None

        if normalized_sex in (
            "m",
            "male",
            "man",
            "boy",
        ):

            gender = "M"

        elif normalized_sex in (
            "f",
            "female",
            "woman",
            "girl",
        ):

            gender = "F"

        else:

            gender = normalized_sex

        # =================================================
        # BUILD V2 INPUT
        # =================================================

        
        ml_input = {

            "age": patient.get(
                "age"
            ),

            "gender": gender,

            "temperature": vitals.get(
                "temperature"
            ),

            "heartrate": vitals.get(
                "heart_rate",
                vitals.get("hr")
            ),

            "resprate": vitals.get(
                "respiratory_rate"
            ),

            "o2sat": vitals.get(
                "spo2"
            ),

            "sbp": vitals.get(
                "bp_systolic"
            ),

            "dbp": vitals.get(
                "bp_diastolic"
            ),

            "respiratory_rate": vitals.get(
                "respiratory_rate"
            ),

            "pain": vitals.get(
                "pain"
            ),

            "breathing": patient.get(
                "breathing"
            ),

            "responsiveness": patient.get(
                "responsiveness"
            ),

            "distress_level": patient.get(
                "distress_level"
            ),

            "chiefcomplaint": (
                patient.get(
                    "chief_complaint"
                )
                or ""
            ),
        }

        # =================================================
        # RUN V2 PIPELINE
        # =================================================

        print("\n========== V2 INPUT ==========")
        
        for key, value in ml_input.items():
                    print(f"{key}: {value}")
        
        print("==============================")
        
        result = predict_patient(
            ml_input
        )

        print("\n========== V2 OUTPUT ==========")
        print("RAW ESI:", result.get("ml_raw_acuity"))
        print("FINAL ESI:", result.get("acuity"))
        print("SAFETY:", result.get("safety_decision"))
        print("EMERGENCY:", result.get("emergency_override"))
        print("VITAL INTERPRETER:")
        print(result.get("vital_interpreter"))
        print("===============================\n")

       
        # =================================================
        # REASONING
        # =================================================

        reasoning = []

        vital_interpreter = (
            result.get(
                "vital_interpreter"
            )
            or {}
        )

        # -------------------------------------------------
        # Vital Interpreter reasoning
        # -------------------------------------------------

        reasoning.extend(
            vital_interpreter.get(
                "reasoning",
                []
            )
        )

        # -------------------------------------------------
        # Safety / Emergency reasoning
        # -------------------------------------------------

        if result.get(
            "emergency_override"
        ):

            reasoning.extend(
                result.get(
                    "emergency_reasons",
                    []
                )
            )

        else:

            reasoning.extend(
                result.get(
                    "safety_reasons",
                    []
                )
            )

        # -------------------------------------------------
        # Missing data
        # -------------------------------------------------

        missing_fields = result.get(
            "missing_fields",
            []
        )

        if missing_fields:

            reasoning.append(
                "Missing/incomplete data: "
                + ", ".join(
                    missing_fields
                )
            )

        # =================================================
        # COORDINATOR REVIEW
        # =================================================

        auto_escalate = bool(
            result.get(
                "emergency_override"
            )
            or result.get(
                "clinician_review_required"
            )
            or result.get(
                "safety_decision"
            ) == "SAFETY_ESCALATION"
        )

        # =================================================
        # CONFIDENCE
        # =================================================

        confidence = result.get(
            "confidence"
        )

        # =================================================
        # EXISTING RESULT FORMAT
        # =================================================

        assessment = {

            # Final safety-adjusted ESI
            "esi_level": result[
                "acuity"
            ],

            # ML confidence.
            # Emergency override may return None.
            "confidence": confidence,

            # Kept for existing DB/frontend compatibility.
            "confidence_band": _confidence_band(
                confidence
            ),

            # Structured explanation
            "reasoning": reasoning,

            # Coordinator review
            "auto_escalate_for_coordinator_review":
                auto_escalate,

            # =================================================
            # INTERNAL V2 FIELDS
            # =================================================

            "ml_raw_esi_level":
                result.get(
                    "ml_raw_acuity"
                ),

            "safety_decision":
                result.get(
                    "safety_decision"
                ),

            "data_completeness":
                result.get(
                    "data_completeness"
                ),

            "decision_reliability":
                result.get(
                    "decision_reliability"
                ),

            "vital_interpreter":
                vital_interpreter,

            "probabilities":
                result.get(
                    "probabilities"
                ),

            "emergency_override":
                result.get(
                    "emergency_override",
                    False
                ),

            "emergency_reasons":
                result.get(
                    "emergency_reasons",
                    []
                ),
        }

        return assessment