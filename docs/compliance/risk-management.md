# Risk management: PatientTriage.ai

| | |
| --- | --- |
| Provider | Nekod Test Labs B.V. |
| System | PatientTriage.ai, release 1.0.0, model `catboost_esi_model_v3.joblib` |
| Owner | Clinical ML Lead |
| Part of | QMS manual, section 9 (`quality-management-system.md`) |
| Method | ISO/IEC 23894:2023 |

This is the risk management system of Article 9 for PatientTriage.ai: the procedure, the risk
register and the log of every review.

## Procedure

1. **Identify** the hazards of the AI function in its intended use: a coordinator in an emergency
   department ranking patients by the ESI the system recommends. Sources: the design, the release
   validation, problem reports, the audit trail and the Clinical Safety Officer.
2. **Estimate** each risk: severity (1 negligible to 5 catastrophic) times likelihood (1 rare to
   5 frequent).
3. **Evaluate**: a score of 10 or more is not acceptable without a control.
4. **Control** the risk in the design first, then by information to the coordinator, then by
   instructions to the deployer. Record the residual score.
5. **Accept**: the Managing Director accepts the overall residual risk before each release.
6. **Review**:
   - every quarter (next due 2026-12-14),
   - for every significant change under the change procedure (QMS manual, section 4),
   - within 5 working days after a possible serious incident.
   Each review adds a dated entry to the log below.

## Risk register

| ID | Hazard | Harm | Before (S x L) | Controls | Evidence | After (S x L) | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| R1 | Model under-triages a patient with an immediate life threat | Delayed resuscitation, death | 5 x 3 = 15 | Safety Engine ESI-1 override on objective emergency signs; coordinator review | `_objective_emergency` in `development/ml/predict.py`; `development/tests/test_safety_engine.py` | 5 x 1 = 5 | Controlled |
| R2 | Model places a high-risk complaint (chest pain, stroke, sepsis) at ESI-3 or lower | Delayed treatment | 4 x 3 = 12 | High-risk guard raises to ESI-2 | `_high_risk_non_emergency` in `predict.py`; test `test_chest_pain_with_stable_vitals_is_never_below_esi2` | 4 x 1 = 4 | Controlled |
| R3 | Missing intake data gives a confident-looking recommendation | Wrong priority trusted | 4 x 3 = 12 | Confidence reduced with missing fields; reliability shown; clinician review required below 65% completeness or with unknown categories | `_confidence` and missing-data rules in `predict.py` | 4 x 2 = 8 | Controlled |
| R4 | Child or older patient's vitals read with adult thresholds | Under- or over-triage | 4 x 3 = 12 | Age-aware Vital Interpreter is written but `predict.py` does not call it yet (found 2026-06-03); until it is wired in, the instructions for use tell coordinators to check vitals of patients under 18 and over 65 themselves | `development/services/vital_interpreter.py` (not reached); `instructions-for-use.md`, section 4 | 4 x 2 = 8 | Open, wiring planned for 1.1.0 |
| R5 | Coordinator accepts the AI ESI without checking (automation bias) | Model error passes unchecked | 4 x 3 = 12 | AI system notice; confirm or override with a reason; audit trail; override rate reviewed quarterly | `frontend/src/components/AiDisclosure.tsx`; `development/routes/coordinator_review.py` | 4 x 2 = 8 | Controlled |
| R6 | Patient deteriorates in the waiting queue after triage | Delayed care | 5 x 3 = 15 | Time-based and event-driven re-triage | `development/services/retriage_service.py`, `retriage_scheduler.py` | 5 x 1 = 5 | Controlled |
| R7 | A missing respiratory rate is read as 0 and triggers the "not breathing" ESI-1 override | Over-triage, a bed taken from another patient | 2 x 3 = 6 | Coordinator review shows the emergency reason; fix planned for 1.1.0 (treat missing as missing) | `predict.py`, `_objective_emergency`, resprate check | 2 x 3 = 6 | Open, accepted until 1.1.0 |
| R8 | Population drift: the model was trained on US data (MIMIC-IV-ED Demo) | Accuracy lower than validated | 4 x 3 = 12 | Quarterly re-evaluation against coordinator-confirmed ESI levels | QMS manual, section 6 | 4 x 2 = 8 | Controlled |
| R9 | A different model file is loaded than the one validated | Unvalidated behaviour | 5 x 2 = 10 | Only v3 is in the repository; SHA-256 checked in `ci` | `.github/workflows/ci.yml` | 5 x 1 = 5 | Controlled |
| R10 | A Hindi interface string changes the clinical meaning | Wrong action by coordinator | 3 x 2 = 6 | Bilingual clinician reviews new strings before release | `frontend/src/context/LanguageContext.tsx` | 3 x 1 = 3 | Controlled |
| R11 | The API has no authentication | Patient data read or changed by someone on the network | 4 x 3 = 12 | Instructions for use require deployment on the hospital's internal network behind its access control | `instructions-for-use.md`, section 6 | 4 x 2 = 8 | Open, sign-in planned for 1.1.0 |

## Review log

| Date | Trigger | Release | What changed | By |
| --- | --- | --- | --- | --- |
| 2026-02-16 | Register created | 0.8.0 | R1 to R4 identified; R1 to R3 controlled with the Safety Engine | Clinical ML Lead, Clinical Safety Officer |
| 2026-04-14 | Significant change: re-triage and coordinator review | 0.9.0 | R5 and R6 added; R10 added for the Hindi interface | Clinical ML Lead |
| 2026-06-03 | Pre-release review | 1.0.0 | R7, R8, R9 and R11 added; R4 reopened (Vital Interpreter not called); AI system notice added as a control for R5; all scores reviewed | Clinical ML Lead, Clinical Safety Officer |
| 2026-06-04 | Acceptance | 1.0.0 | Overall residual risk accepted; R4, R7 and R11 accepted until 1.1.0 | Managing Director |
| 2026-09-14 | Quarterly review | 1.0.0 | 2 problem reports, none a possible serious incident; quarterly re-evaluation within release targets; no score changed | Clinical ML Lead |
