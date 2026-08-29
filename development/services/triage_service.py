from services.triage_model import TriageModel


def run_triage_assessment(
    patient,
    event_context=None
):
    """
    Convert SQLAlchemy Patient into the ML patient schema.

    The ML model uses the actual numerical vital signs:
    temperature, HR, RR, SpO2, SBP, DBP and pain,
    plus gender and chief complaint.
    """

    patient_dict = {

        "age": patient.age,

        "sex": patient.sex,

        "chief_complaint":
            patient.chief_complaint,

        "vitals": {

            "spo2":
                patient.spo2,

            "bp_systolic":
                patient.bp_systolic,

            "bp_diastolic":
                patient.bp_diastolic,

            "hr":
                patient.heart_rate,

            "respiratory_rate":
                patient.respiratory_rate,

            "temperature":
                patient.temperature,

            "pain":
                patient.pain
        },

        "observed": {},

        "history": {},

        "clarifying_answers": {}
    }

    # -----------------------------------------------------
    # RETRIAGE / NEW VITALS
    # -----------------------------------------------------

    if event_context:

        patient_dict["event_context"] = (
            event_context
        )

        new_vitals = (
            event_context
            .get("data", {})
            .get("new_vitals")
        )

        if new_vitals:

            patient_dict["vitals"].update({

                "spo2":
                    new_vitals.get(
                        "spo2",
                        patient_dict["vitals"]["spo2"]
                    ),

                "bp_systolic":
                    new_vitals.get(
                        "bp_systolic",
                        patient_dict["vitals"]["bp_systolic"]
                    ),

                "bp_diastolic":
                    new_vitals.get(
                        "bp_diastolic",
                        patient_dict["vitals"]["bp_diastolic"]
                    ),

                "hr":
                    new_vitals.get(
                        "heart_rate",
                        patient_dict["vitals"]["hr"]
                    ),

                "respiratory_rate":
                    new_vitals.get(
                        "respiratory_rate",
                        patient_dict["vitals"]["respiratory_rate"]
                    ),

                "temperature":
                    new_vitals.get(
                        "temperature",
                        patient_dict["vitals"]["temperature"]
                    ),

                "pain":
                    new_vitals.get(
                        "pain",
                        patient_dict["vitals"]["pain"]
                    )
            })

    # -----------------------------------------------------
    # RUN ML MODEL
    # -----------------------------------------------------

    return TriageModel().assess_patient(
        patient_dict
    )