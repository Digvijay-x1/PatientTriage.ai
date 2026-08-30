import requests

BASE_URL = "http://127.0.0.1:5000/api"


def test_patient(name, data):
    print("\n" + "=" * 70)
    print(name)
    print("=" * 70)

    print("\nINPUT:")
    for key, value in data.items():
        print(f"{key}: {value}")

    response = requests.post(
        f"{BASE_URL}/patients",
        json=data,
    )

    print("\nHTTP STATUS:", response.status_code)

    try:
        result = response.json()
        print("\nBACKEND RESPONSE:")
        print(result)
    except Exception:
        print(response.text)


# ============================================================
# CASE 1: CLEAR LOW-ACUITY PATIENT
# ============================================================

low_acuity = {
    "patient_id": "TEST_LOW_006",
    "age": 20,
    "sex": "male",
    "chief_complaint": "headache",

    "vitals": {
        "spo2": 92,
        "bp_systolic": 120,
        "bp_diastolic": 80,
        "heart_rate": 99,
        "respiratory_rate": 24,
        "temperature": 36.8,
        "pain": 1,
    },

    "observed": {
        "responsiveness": "alert",
        "breathing": "normal",
        "distress_level": "low",
    },

    "has_prior_record": False,
    "history_cardiac": True,
    "history_respiratory": False,
    "history_diabetes": False,
    "history_renal": False,
    "history_hypertension": False,
}


# ============================================================
# CASE 2: CLEAR EMERGENCY
# ============================================================

emergency = {
    "patient_id": "TEST_EMERGENCY_00",
    "age": 55,
    "sex": "male",
    "chief_complaint": "severe difficulty breathing",

    "vitals": {
        "spo2": 60,
        "bp_systolic": 50,
        "bp_diastolic": 30,
        "heart_rate": 0,
        "respiratory_rate": 0,
        "temperature": 36,
        "pain": 0,
    },

    "observed": {
        "responsiveness": "unresponsive",
        "breathing": "absent",
        "distress_level": "severe",
    },

    "has_prior_record": False,
    "history_cardiac": False,
    "history_respiratory": False,
    "history_diabetes": False,
    "history_renal": False,
    "history_hypertension": False,
}


# ============================================================
# RUN
# ============================================================

test_patient(
    "TEST CASE 1: LOW ACUITY",
    low_acuity,
)

test_patient(
    "TEST CASE 2: EMERGENCY",
    emergency,
)