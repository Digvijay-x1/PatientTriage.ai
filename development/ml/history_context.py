"""
PatientTriage.ai - History Context Layer

Interprets a patient's known prior-history comorbidity flags against
their current chief complaint, to surface clinically relevant
condition-complaint combinations for the Safety Engine.

This module does NOT touch the frozen CatBoost model or its 12-input
schema. It is an additional signal layer, following the same pattern
as the Vital Interpreter: a self-contained module that returns
structured output for `_safety_adjustment` to read.

Design assumption (stated, not modeled): roughly half of arriving
patients have some prior record on file and half do not. All new
fields below default to absent/False, so a patient dict that omits
them reproduces the exact pre-history-layer behavior -- this keeps the
20/20 edge-case regression suite (round2_edge_case_test.py) unchanged
for any caller that doesn't opt in.

IMPORTANT: The condition-complaint associations below are common-sense
clinical heuristics chosen for this prototype/demo. They are not
derived from a validated clinical decision rule (e.g. not sourced from
a peer-reviewed risk score) and must not be presented as such. A real
deployment needs clinician-authored, evidence-based history-risk rules.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class HistoryFlag:
    condition: str
    matched_terms: List[str]
    reasoning: str


@dataclass
class HistoryResult:
    has_prior_record: bool
    conditions_present: List[str] = field(default_factory=list)
    relevant_flags: List[HistoryFlag] = field(default_factory=list)

    @property
    def has_relevant_risk(self) -> bool:
        return bool(self.relevant_flags) 


# Condition -> chief-complaint keywords that make that condition
# clinically relevant to the current presentation.
_CONDITION_COMPLAINT_TERMS = {
    "cardiac": [
        "chest pain", "chest discomfort", "chest tightness",
        "palpitation", "shortness of breath", "syncope", "fainting",
    ],
    "respiratory": [
        "breathing", "breath", "wheeze", "wheezing", "cough", "asthma",
    ],
    "diabetes": [
        "weakness", "confusion", "dizziness", "abdominal pain",
        "nausea", "vomiting",
    ],
    "renal": [
        "swelling", "shortness of breath", "fatigue", "nausea",
    ],
    "hypertension": [
        "headache", "dizziness", "weakness", "confusion", "vision",
    ],
}

# Patient dict key for each comorbidity flag.
_CONDITION_KEYS = {
    "cardiac": "history_cardiac",
    "respiratory": "history_respiratory",
    "diabetes": "history_diabetes",
    "renal": "history_renal",
    "hypertension": "history_hypertension",
}


def evaluate_history(patient: dict) -> HistoryResult:
    """Build a HistoryResult from optional patient fields.

    Expected optional patient keys (all default to False if absent):
        has_prior_record: bool
        history_cardiac, history_respiratory, history_diabetes,
        history_renal, history_hypertension: bool
    """
    has_prior_record = bool(patient.get("has_prior_record", False))

    conditions_present = [
        cond for cond, key in _CONDITION_KEYS.items()
        if has_prior_record and bool(patient.get(key, False))
    ]

    complaint = str(patient.get("chiefcomplaint") or "").strip().lower()
    relevant_flags = []
    if complaint:
        for cond in conditions_present:
            terms = _CONDITION_COMPLAINT_TERMS.get(cond, [])
            matched = [t for t in terms if t in complaint]
            if matched:
                relevant_flags.append(HistoryFlag(
                    condition=cond,
                    matched_terms=matched,
                    reasoning=(
                        f"history of {cond} disease with a presenting "
                        f"complaint consistent with {cond} decompensation"
                    ),
                ))

    return HistoryResult(
        has_prior_record=has_prior_record,
        conditions_present=conditions_present,
        relevant_flags=relevant_flags,
    )
