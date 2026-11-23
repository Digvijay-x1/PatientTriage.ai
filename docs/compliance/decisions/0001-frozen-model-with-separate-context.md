# 0001: Keep the CatBoost model frozen and put context outside it

- Date: 2026-02-20
- Status: Accepted
- Deciders: Clinical ML Lead, Clinical Safety Officer

## Context

Patient history and facility type help a coordinator, but adding them as model inputs would change
the model's learned behaviour every time a deployer's context changes, and each change would need a
new validation.

## Decision

`catboost_esi_model_v3.joblib` is frozen with the 12 inputs in the README, section 4. History
(`development/ml/history_context.py`) and facility context are separate layers that never change
the model input. A new model artifact is a significant change (QMS manual, section 4).

## Consequences

Validation results stay valid until the artifact changes. `ci` checks the artifact's SHA-256.
