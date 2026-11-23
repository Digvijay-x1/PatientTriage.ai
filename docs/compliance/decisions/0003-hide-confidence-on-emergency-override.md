# 0003: Hide model confidence after an emergency override

- Date: 2026-02-24
- Status: Accepted
- Deciders: Clinical ML Lead, Frontend Lead

## Context

After the Safety Engine forces ESI-1, the model's probability no longer describes the decision.
Showing it would invite the coordinator to weigh a number that did not decide anything.

## Decision

`predict_patient` returns `confidence = None` on an emergency override, the backend sets the band to
`emergency_override`, and the Coordinator Review dialog shows "N/A" and "Emergency Override".

## Consequences

Coordinators see why the ESI is 1 (the emergency reasons) instead of a probability.
