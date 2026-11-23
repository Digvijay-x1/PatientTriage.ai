# Regression tests for the frozen CatBoost model and the Safety Engine in
# ml/predict.py. Continuous integration runs them on every change
# (.github/workflows/ci.yml). They are the release tests named in
# docs/compliance/quality-management-system.md, section 5.
import pytest

from ml.predict import predict_patient


def patient(**overrides):
    base = {
        "temperature": 36.8,
        "heartrate": 82,
        "resprate": 16,
        "o2sat": 98,
        "sbp": 124,
        "dbp": 78,
        "pain": 2,
        "gender": "F",
        "breathing": "normal",
        "responsiveness": "alert",
        "distress_level": "low",
        "chiefcomplaint": "mild headache",
    }
    base.update(overrides)
    return base


def test_unresponsive_patient_gets_esi1_emergency_override_with_hidden_confidence():
    result = predict_patient(patient(
        heartrate=40,
        resprate=0,
        o2sat=70,
        sbp=70,
        dbp=40,
        pain=0,
        breathing="absent",
        responsiveness="unresponsive",
        distress_level="severe",
        chiefcomplaint="cardiac arrest",
    ))

    assert result["acuity"] == 1
    assert result["emergency_override"] is True
    assert result["confidence"] is None
    assert result["safety_decision"] == "IMMEDIATE_EMERGENCY"


def test_chest_pain_with_stable_vitals_is_never_below_esi2():
    result = predict_patient(patient(
        pain=6,
        distress_level="moderate",
        chiefcomplaint="chest pain",
    ))

    assert result["acuity"] == 2
    assert result["emergency_override"] is False


def test_unknown_category_requires_clinician_review():
    result = predict_patient(patient(gender=None))

    assert "gender" in result["missing_fields"]
    assert result["clinician_review_required"] is True
    assert result["safety_decision"] == "SAFETY_ESCALATION"


def test_probabilities_cover_all_five_esi_levels():
    result = predict_patient(patient())

    assert set(result["probabilities"]) == {"1", "2", "3", "4", "5"}
    assert abs(sum(result["probabilities"].values()) - 1.0) < 1e-6


@pytest.mark.parametrize(
    "field,value",
    [
        ("temperature", 50.0),
        ("o2sat", 120),
        ("pain", 11),
    ],
)
def test_impossible_vitals_are_rejected(field, value):
    with pytest.raises(ValueError):
        predict_patient(patient(**{field: value}))


def test_unknown_breathing_value_is_rejected():
    with pytest.raises(ValueError):
        predict_patient(patient(breathing="gasping"))
