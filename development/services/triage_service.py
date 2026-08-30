from services.triage_model import TriageModel


def run_triage_assessment(
    patient,
    event_context=None
):
    """
    Run the V2 triage pipeline and convert the SQLAlchemy
    Patient into the schema expected by TriageModel.
    """

    patient_dict = {
        "age": patient.age,
        "sex": patient.sex,
        "chief_complaint": patient.chief_complaint,

        "vitals": {
            "spo2": patient.spo2,
            "bp_systolic": patient.bp_systolic,
            "bp_diastolic": patient.bp_diastolic,
            "hr": patient.heart_rate,
            "respiratory_rate": patient.respiratory_rate,
            "temperature": patient.temperature,
            "pain": patient.pain,
        },

        "breathing": getattr(
            patient,
            "breathing",
            None,
        ),

        "responsiveness": getattr(
            patient,
            "responsiveness",
            None,
        ),

        "distress_level": getattr(
            patient,
            "distress_level",
            None,
        ),

        "observed": {},
        "history": {},
        "clarifying_answers": {},
    }

    # =====================================================
    # RE-TRIAGE / NEW VITALS
    # =====================================================

    if event_context:

        new_vitals = (
            event_context
            .get("data", {})
            .get("new_vitals")
        )

        if new_vitals:

            patient_dict["vitals"].update({
                "spo2": new_vitals.get(
                    "spo2",
                    patient_dict["vitals"]["spo2"],
                ),

                "bp_systolic": new_vitals.get(
                    "bp_systolic",
                    patient_dict["vitals"]["bp_systolic"],
                ),

                "bp_diastolic": new_vitals.get(
                    "bp_diastolic",
                    patient_dict["vitals"]["bp_diastolic"],
                ),

                "hr": new_vitals.get(
                    "heart_rate",
                    patient_dict["vitals"]["hr"],
                ),

                "respiratory_rate": new_vitals.get(
                    "respiratory_rate",
                    patient_dict["vitals"]["respiratory_rate"],
                ),

                "temperature": new_vitals.get(
                    "temperature",
                    patient_dict["vitals"]["temperature"],
                ),

                "pain": new_vitals.get(
                    "pain",
                    patient_dict["vitals"]["pain"],
                ),
            })

    # =====================================================
    # RUN V2 MODEL
    # =====================================================

    assessment = TriageModel().assess_patient(
        patient_dict
    )

    # =====================================================
    # DEBUG
    # =====================================================

    print("\n========== BACKEND TRIAGE ==========")
    print("FINAL ESI:", assessment.get("esi_level"))
    print("CONFIDENCE:", assessment.get("confidence"))
    print(
        "CONFIDENCE BAND:",
        assessment.get("confidence_band"),
    )
    print(
        "AUTO ESCALATE:",
        assessment.get(
            "auto_escalate_for_coordinator_review"
        ),
    )
    print("====================================\n")

    return assessment