# 0002: Safety rules run after the model, as fixed rules

- Date: 2026-02-24
- Status: Accepted
- Deciders: Clinical ML Lead, Clinical Safety Officer

## Context

A model trained on a small dataset can under-triage rare, critical presentations (risk R1).

## Decision

Fixed rules in `development/ml/predict.py` run after the model: an ESI-1 override on objective
emergency signs (`_objective_emergency`), a guard that raises high-risk complaints to ESI-2
(`_high_risk_non_emergency`), and a clinician-review flag for missing data. A raw model ESI-1
without objective emergency signs is shown as ESI-2.

## Consequences

The safety behaviour can be read and tested without the model
(`development/tests/test_safety_engine.py`). The rules can over-triage (risk R7).
