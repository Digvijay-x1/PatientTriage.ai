# Changelog

Releases of PatientTriage.ai by Nekod Test Labs B.V. A release is placed on the market only
after the steps in `docs/compliance/quality-management-system.md`, section 5.

## 1.0.0, 2026-06-15: first production release

Placed on the market on 2026-06-15. Conformity assessment completed on 2026-06-05
(`docs/compliance/conformity-assessment.md`).

- AI system notice on the dashboard and in every dialog that shows a model recommendation.
- Legal notice with the provider's name and address, the release and the CE marking.
- Coordinators can report a problem with an AI recommendation (`POST /api/incident-reports`).
- Runtime dependencies pinned; CatBoost pinned to 1.2.8, the version the model was saved with.
- Release tests for the Safety Engine run in continuous integration.

## 0.9.0, 2026-04-10: hospital pilot (not placed on the market)

- Re-triage on new vitals and on time in the waiting queue.
- Coordinator confirm and override with a reason, written to the audit trail.
- Hindi interface.

## 0.8.0, 2026-02-27: internal build

- CatBoost model `catboost_esi_model_v3.joblib` frozen.
- Safety Engine: ESI-1 emergency override, high-risk guard, missing-data review.
