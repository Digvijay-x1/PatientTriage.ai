# Technical documentation: PatientTriage.ai 1.0.0

| | |
| --- | --- |
| Provider | Nekod Test Labs B.V., Keizersgracht 100, 1015 CW Amsterdam, the Netherlands |
| System and version | PatientTriage.ai 1.0.0, model `catboost_esi_model_v3.joblib` (SHA-256 `b18fa75c2acf6cd294a9f192dc01235221a240ab5205b0fa53a22437d2d41475`) |
| Owner | Clinical ML Lead |
| Version of this document | 1.0, 2026-06-03 |
| Retention | 10 years, see `documentation-retention.md` |

This file is the technical documentation required by Article 11 and Annex IV. It points to the
code and documents in this repository that hold each part.

## 1. General description (Annex IV, point 1)

- **Intended purpose**: recommend an ESI level (1 to 5) for adult and paediatric patients at
  emergency department intake, and flag patients for re-triage while they wait. Users are trained
  triage coordinators. The coordinator decides the priority.
- **Classification**: high-risk, Article 6(2), Annex III point 5(d).
- **Not intended for**: diagnosis, treatment decisions, use without a coordinator, use outside an
  emergency department.
- **Components**: Flask backend (`development/`), React dashboard (`frontend/`), CatBoost model and
  Safety Engine (`development/ml/predict.py`).
- **Hardware**: a standard x86-64 server at the deployer; no GPU.
- **Instructions for use**: `instructions-for-use.md`.

## 2. Development and design (Annex IV, point 2)

- **Architecture**: README, section 2; decision records in `decisions/`.
- **Model**: CatBoost classifier, 12 inputs (README, section 4), five classes. Frozen since
  release 0.8.0.
- **Safety Engine**: deterministic rules on top of the model output: ESI-1 emergency override,
  high-risk guard, missing-data review, low-acuity routing (`predict.py`).
- **Human oversight**: coordinator confirm or override with a reason
  (`development/routes/coordinator_review.py`), shown in `frontend/src/components/PatientReview.tsx`.
- **Data**: QMS manual, section 8.
- **Validation and testing**: QMS manual, section 6; results in README, section 15;
  tests in `development/tests/`.
- **Cybersecurity**: input validation in `_validate_patient`; deployment on the hospital's internal
  network (instructions for use, section 6). Known gap: no API authentication (risk R11).

## 3. Monitoring, functioning and control (Annex IV, point 3)

- **Performance** on the MIMIC-IV-ED Demo test split: README, section 15.
- **Known limitations**: risks R4, R7, R8 and R11 in `risk-management.md`.
- **Logs**: every assessment, decision, override and re-triage is written to `audit_logs`
  (`development/models/audit_log.py`) and shown in the Audit Trail tab.

## 4. Performance metrics (Annex IV, point 4)

Accuracy, under-triage, severe under-triage and ESI-1 recall, chosen because under-triage is the
harm that matters most in emergency triage. Targets in QMS manual, section 6.

## 5. Risk management (Annex IV, point 5)

`risk-management.md`.

## 6. Changes over the lifecycle (Annex IV, point 6)

`CHANGELOG.md` and the review log in `risk-management.md`.

## 7. Standards applied (Annex IV, point 7)

QMS manual, section 7.

## 8. EU declaration of conformity (Annex IV, point 8)

`eu-declaration-of-conformity.md`.

## 9. Post-market monitoring (Annex IV, point 9)

QMS manual, section 10, and `serious-incident-reporting.md`.
