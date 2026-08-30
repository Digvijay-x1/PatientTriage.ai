from ml.predict import predict_patient


# =========================================================
# BASE PATIENT
# =========================================================

BASE = {
    "age": 40,
    "temperature": 36.8,
    "heartrate": 78,
    "resprate": 16,
    "o2sat": 98,
    "sbp": 120,
    "dbp": 80,
    "pain": 2,
    "gender": "F",
    "breathing": "normal",
    "responsiveness": "alert",
    "distress_level": "low",
    "chiefcomplaint": "headache",

    "has_prior_record": False,
    "history_cardiac": False,
    "history_respiratory": False,
    "history_diabetes": False,
    "history_renal": False,
    "history_hypertension": False,
}


# =========================================================
# HELPER
# =========================================================

def make_patient(
    complaint=None,
    vitals=None,
    history=None,
    observed=None,
):
    patient = BASE.copy()

    if complaint is not None:
        patient["chiefcomplaint"] = complaint

    if vitals:
        patient.update(vitals)

    if history:
        patient.update(history)

    if observed:
        patient.update(observed)

    return patient


def run_test(number, name, patient):

    print("\n" + "=" * 80)
    print(f"TEST {number}: {name}")
    print("=" * 80)

    print("\nINPUT")
    print("-" * 40)

    for key, value in patient.items():
        print(f"{key:22}: {value}")

    try:

        result = predict_patient(patient)

        print("\nMODEL OUTPUT")
        print("-" * 40)

        print(
            "Raw ML ESI          :",
            result.get("ml_raw_acuity")
        )

        print(
            "Final ESI           :",
            result.get("acuity")
        )

        print(
            "Confidence          :",
            result.get("confidence")
        )

        print(
            "Safety Decision     :",
            result.get("safety_decision")
        )

        print(
            "Emergency Override  :",
            result.get("emergency_override")
        )

        print(
            "Clinician Review    :",
            result.get("clinician_review_required")
        )

        print(
            "Data Completeness   :",
            result.get("data_completeness")
        )

        print(
            "Decision Reliability:",
            result.get("decision_reliability")
        )

        # =================================================
        # VITAL INTERPRETER
        # =================================================

        vital = result.get(
            "vital_interpreter"
        ) or {}

        print("\nVITAL INTERPRETER")
        print("-" * 40)

        print(
            "Available       :",
            vital.get("available")
        )

        print(
            "Age Group       :",
            vital.get("age_group")
        )

        print(
            "Critical Count  :",
            vital.get("critical_count")
        )

        print(
            "Urgent Count    :",
            vital.get("urgent_count")
        )

        if vital.get("reasoning"):

            print("\nVital Reasoning:")

            for reason in vital["reasoning"]:
                print("  -", reason)

        # =================================================
        # HISTORY
        # =================================================

        history = result.get(
            "history_context"
        )

        print("\nHISTORY CONTEXT")
        print("-" * 40)

        if history:

            print(
                "Prior Record:",
                history.get("has_prior_record")
            )

            print(
                "Conditions:",
                history.get("conditions_present")
            )

            print(
                "Relevant Risk:",
                history.get("has_relevant_risk")
            )

            flags = history.get(
                "relevant_flags",
                []
            )

            if flags:

                print("\nRelevant History Flags:")

                for flag in flags:
                    print(
                        "  -",
                        flag
                    )

        else:

            print("No history context returned.")

        # =================================================
        # SAFETY REASONING
        # =================================================

        print("\nSAFETY REASONING")
        print("-" * 40)

        safety_reasons = result.get(
            "safety_reasons",
            []
        )

        if safety_reasons:

            for reason in safety_reasons:
                print("  -", reason)

        else:

            print("None")

        # =================================================
        # EMERGENCY REASONS
        # =================================================

        emergency_reasons = result.get(
            "emergency_reasons",
            []
        )

        if emergency_reasons:

            print("\nEMERGENCY REASONS")
            print("-" * 40)

            for reason in emergency_reasons:
                print("  -", reason)

    except Exception as e:

        print("\nERROR")
        print("-" * 40)
        print(type(e).__name__, e)


# =========================================================
# TEST CASES
# =========================================================

tests = [

    # -----------------------------------------------------
    # 1. NO HISTORY
    # -----------------------------------------------------

    (
        "Stable patient - no history",

        make_patient(
            complaint="headache"
        )
    ),


    # -----------------------------------------------------
    # 2. CARDIAC
    # -----------------------------------------------------

    (
        "Cardiac history + chest pain",

        make_patient(
            complaint="chest pain",

            history={
                "has_prior_record": True,
                "history_cardiac": True,
            }
        )
    ),


    # -----------------------------------------------------
    # 3. RESPIRATORY
    # -----------------------------------------------------

    (
        "Respiratory history + shortness of breath",

        make_patient(
            complaint="shortness of breath",

            history={
                "has_prior_record": True,
                "history_respiratory": True,
            }
        )
    ),


    # -----------------------------------------------------
    # 4. DIABETES
    # -----------------------------------------------------

    (
        "Diabetes history + nausea",

        make_patient(
            complaint="nausea and vomiting",

            history={
                "has_prior_record": True,
                "history_diabetes": True,
            }
        )
    ),


    # -----------------------------------------------------
    # 5. RENAL
    # -----------------------------------------------------

    (
        "Renal history + swelling",

        make_patient(
            complaint="swelling",

            history={
                "has_prior_record": True,
                "history_renal": True,
            }
        )
    ),


    # -----------------------------------------------------
    # 6. HYPERTENSION
    # -----------------------------------------------------

    (
        "Hypertension history + headache",

        make_patient(
            complaint="headache",

            history={
                "has_prior_record": True,
                "history_hypertension": True,
            }
        )
    ),


    # -----------------------------------------------------
    # 7. ALL FIVE
    # -----------------------------------------------------

    (
        "All five conditions + shortness of breath",

        make_patient(
            complaint="shortness of breath",

            history={
                "has_prior_record": True,
                "history_cardiac": True,
                "history_respiratory": True,
                "history_diabetes": True,
                "history_renal": True,
                "history_hypertension": True,
            }
        )
    ),


    # -----------------------------------------------------
    # 8. CARDIAC + RESPIRATORY
    # -----------------------------------------------------

    (
        "Cardiac + respiratory history",

        make_patient(
            complaint="shortness of breath",

            history={
                "has_prior_record": True,
                "history_cardiac": True,
                "history_respiratory": True,
            }
        )
    ),


    # -----------------------------------------------------
    # 9. DIABETES + RENAL
    # -----------------------------------------------------

    (
        "Diabetes + renal history",

        make_patient(
            complaint="nausea",

            history={
                "has_prior_record": True,
                "history_diabetes": True,
                "history_renal": True,
            }
        )
    ),


    # -----------------------------------------------------
    # 10. HYPERTENSION + CARDIAC
    # -----------------------------------------------------

    (
        "Hypertension + cardiac history",

        make_patient(
            complaint="chest discomfort",

            history={
                "has_prior_record": True,
                "history_cardiac": True,
                "history_hypertension": True,
            }
        )
    ),


    # =====================================================
    # VITAL TESTS
    # =====================================================

    # -----------------------------------------------------
    # 11. COMPLETELY NORMAL
    # -----------------------------------------------------

    (
        "Completely normal vitals",

        make_patient(
            complaint="mild headache"
        )
    ),


    # -----------------------------------------------------
    # 12. LOW SPO2
    # -----------------------------------------------------

    (
        "Low oxygen saturation",

        make_patient(
            complaint="shortness of breath",

            vitals={
                "o2sat": 89,
                "heartrate": 110,
                "resprate": 24,
            },

            observed={
                "breathing": "laboured",
                "distress_level": "high",
            }
        )
    ),


    # -----------------------------------------------------
    # 13. CRITICAL SPO2
    # -----------------------------------------------------

    (
        "Critical oxygen saturation",

        make_patient(
            complaint="difficulty breathing",

            vitals={
                "o2sat": 70,
                "heartrate": 130,
                "resprate": 30,
            },

            observed={
                "breathing": "laboured",
                "distress_level": "high",
            }
        )
    ),


    # -----------------------------------------------------
    # 14. SEVERE HYPOTENSION
    # -----------------------------------------------------

    (
        "Severe hypotension",

        make_patient(
            complaint="severe weakness",

            vitals={
                "sbp": 70,
                "dbp": 30,
                "heartrate": 50,
                "o2sat": 70,
            },

            observed={
                "distress_level": "high",
            }
        )
    ),


    # -----------------------------------------------------
    # 15. EXTREME TACHYCARDIA
    # -----------------------------------------------------

    (
        "Extreme tachycardia",

        make_patient(
            complaint="palpitations",

            vitals={
                "heartrate": 150,
                "resprate": 28,
            },

            observed={
                "distress_level": "high",
            }
        )
    ),


    # -----------------------------------------------------
    # 16. ABSENT BREATHING
    # -----------------------------------------------------

    (
        "Absent breathing",

        make_patient(
            complaint="unresponsive patient",

            vitals={
                "heartrate": 0,
                "resprate": 0,
                "o2sat": 50,
                "sbp": 60,
                "dbp": 30,
            },

            observed={
                "breathing": "absent",
                "responsiveness": "unresponsive",
                "distress_level": "high",
            }
        )
    ),


    # =====================================================
    # HISTORY + VITAL COMBINATION
    # =====================================================

    (
        "Hypertension + headache + abnormal BP",

        make_patient(
            complaint="headache",

            vitals={
                "sbp": 168,
                "dbp": 110,
            },

            history={
                "has_prior_record": True,
                "history_hypertension": True,
            }
        )
    ),


    (
        "Cardiac history + chest pain + tachycardia",

        make_patient(
            complaint="chest pain",

            vitals={
                "heartrate": 135,
                "sbp": 150,
            },

            history={
                "has_prior_record": True,
                "history_cardiac": True,
            },

            observed={
                "distress_level": "high",
            }
        )
    ),


    (
        "Respiratory history + hypoxia",

        make_patient(
            complaint="shortness of breath",

            vitals={
                "o2sat": 82,
                "resprate": 30,
            },

            history={
                "has_prior_record": True,
                "history_respiratory": True,
            },

            observed={
                "breathing": "laboured",
                "distress_level": "high",
            }
        )
    ),


    (
        "Diabetes + vomiting + weakness",

        make_patient(
            complaint="weakness, nausea and vomiting",

            history={
                "has_prior_record": True,
                "history_diabetes": True,
            }
        )
    ),


    (
        "Renal history + swelling + shortness of breath",

        make_patient(
            complaint="swelling and shortness of breath",

            history={
                "has_prior_record": True,
                "history_renal": True,
            }
        )
    ),


    # =====================================================
    # INCOMPLETE DATA
    # =====================================================

    (
        "Missing respiratory rate",

        make_patient(
            complaint="headache",

            vitals={
                "resprate": None,
            }
        )
    ),


    (
        "Missing pain",

        make_patient(
            complaint="headache",

            vitals={
                "pain": None,
            }
        )
    ),


    (
        "Multiple missing vitals",

        make_patient(
            complaint="headache",

            vitals={
                "resprate": None,
                "pain": None,
                "sbp": None,
                "dbp": None,
            }
        )
    ),
]


# =========================================================
# EXECUTE
# =========================================================

print("\n")
print("#" * 80)
print("PATIENTTRIAGE.AI - COMPLETE V2 PIPELINE TEST")
print("#" * 80)

for i, (name, patient) in enumerate(tests, 1):
    run_test(
        i,
        name,
        patient
    )

print("\n")
print("#" * 80)
print("ALL TESTS COMPLETE")
print("#" * 80)