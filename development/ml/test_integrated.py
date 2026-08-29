"""
PatientTriage.ai
Integrated End-to-End Testing

Tests:
1. Normal adult
2. Adult respiratory distress
3. Pediatric patient with fever + BP
4. Geriatric patient with fever/confusion
5. Adult borderline case
"""

from development.ml.predict_esi import predict_esi


def print_result(name, result):

    print("\n" + "=" * 70)
    print(name)
    print("=" * 70)

    print("\nML PREDICTION")
    print("-" * 40)

    print("ML ESI:", result["ml_esi"])
    print("ML Confidence:", result["confidence"])
    print("ML Probabilities:", result.get("probabilities", {}))
    print("Final ESI:", result["esi"])

    print("\nVITAL INTERPRETER")
    print("-" * 40)

    for vital in result["vital_results"]:

        if isinstance(vital, dict):

            vital_name = vital.get("vital_name", "unknown")
            status = vital.get("status", "unknown")

            if vital_name == "pediatric_blood_pressure":

                print(
                    f"{vital_name:28s} "
                    f"SBP={vital.get('systolic_bp')} "
                    f"DBP={vital.get('diastolic_bp')} "
                    f"-> {status.upper()}"
                )

            else:

                print(
                    f"{vital_name:28s} "
                    f"-> {status.upper()}"
                )

        else:

            print(
                f"{vital.vital_name:28s} "
                f"{vital.value:8} "
                f"-> {vital.status.upper()}"
            )

    print("\nCritical flags:", result["critical_flags"])
    print("Urgent flags:", result["urgent_flags"])

    print("\nREASONING")
    print("-" * 40)

    if result["reasoning"]:
        for reason in result["reasoning"]:
            print("-", reason)
    else:
        print("No abnormal vital signs detected.")

    print("\nSAFETY ENGINE")
    print("-" * 40)

    if result["safety_alerts"]:
        for alert in result["safety_alerts"]:
            print("WARNING:", alert)
    else:
        print("No safety alerts.")


# ============================================================
# TEST 1 — NORMAL ADULT
# ============================================================

result_1 = predict_esi(
    vitals={
        "spo2": 98,
        "heart_rate": 75,
        "respiratory_rate": 16,
        "systolic_bp": 120,
        "diastolic_bp": 80,
        "temperature": 36.8,
        "pain": 2
    },
    age=35,
    sex="male",
    chiefcomplaint="mild headache"
)

print_result(
    "TEST 1 — NORMAL ADULT",
    result_1
)


# ============================================================
# TEST 2 — ADULT RESPIRATORY DISTRESS
# ============================================================

result_2 = predict_esi(
    vitals={
        "spo2": 88,
        "heart_rate": 115,
        "respiratory_rate": 32,
        "systolic_bp": 155,
        "diastolic_bp": 90,
        "temperature": 37.2,
        "pain": 7
    },
    age=52,
    sex="male",
    chiefcomplaint="difficulty breathing"
)

print_result(
    "TEST 2 — ADULT RESPIRATORY DISTRESS",
    result_2
)


# ============================================================
# TEST 3 — PEDIATRIC FEVER + AAP BP
# ============================================================

result_3 = predict_esi(
    vitals={
        "spo2": 97,
        "heart_rate": 110,
        "respiratory_rate": 28,
        "systolic_bp": 112,
        "diastolic_bp": 70,
        "temperature": 39.2,
        "pain": 6
    },
    age=8,
    sex="male",
    chiefcomplaint="fever"
)

print_result(
    "TEST 3 — PEDIATRIC FEVER + AAP BP",
    result_3
)


# ============================================================
# TEST 4 — GERIATRIC
# ============================================================

result_4 = predict_esi(
    vitals={
        "spo2": 93,
        "heart_rate": 106,
        "respiratory_rate": 26,
        "systolic_bp": 142,
        "diastolic_bp": 82,
        "temperature": 38.2,
        "pain": 4
    },
    age=78,
    sex="female",
    chiefcomplaint="weakness and confusion"
)

print_result(
    "TEST 4 — GERIATRIC FEVER + CONFUSION",
    result_4
)


# ============================================================
# TEST 5 — BORDERLINE ADULT
# ============================================================

result_5 = predict_esi(
    vitals={
        "spo2": 95,
        "heart_rate": 102,
        "respiratory_rate": 24,
        "systolic_bp": 145,
        "diastolic_bp": 92,
        "temperature": 38.0,
        "pain": 5
    },
    age=45,
    sex="female",
    chiefcomplaint="chest discomfort"
)

print_result(
    "TEST 5 — BORDERLINE ADULT",
    result_5
)


print("\n" + "=" * 70)
print("ALL INTEGRATED TESTS COMPLETE")
print("=" * 70)
