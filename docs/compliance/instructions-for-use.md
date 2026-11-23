# Instructions for use: PatientTriage.ai 1.0.0

![CE marking](../../frontend/public/ce-mark.svg)

**Provider**: Nekod Test Labs B.V., Keizersgracht 100, 1015 CW Amsterdam, the Netherlands.
Contact: compliance@nekod-testlabs.example

CE marked high-risk AI system under Regulation (EU) 2024/1689. EU database registration
EUDB-HR-2026-0042-PT. EU declaration of conformity: `eu-declaration-of-conformity.md`.

## 1. What it is for

PatientTriage.ai recommends an Emergency Severity Index (ESI) level from 1 (immediate) to 5
(non-urgent) for patients arriving at an emergency department, and flags waiting patients for
re-triage. It is used by trained triage coordinators. The coordinator decides the patient's priority.
Do not use it for diagnosis, for treatment decisions, or without a coordinator.

## 2. How it works

A machine-learning model (CatBoost) reads 12 intake values and gives an ESI with its probabilities.
Fixed safety rules then raise the ESI for an immediate emergency or a high-risk complaint, and ask
for clinician review when data is missing. The dashboard tells the coordinator that the
recommendation comes from an AI system.

## 3. Performance

On the MIMIC-IV-ED Demo test split: accuracy 92.27%, under-triage 2.90%, severe under-triage
0.00%, ESI-1 recall 88.89% (README, section 15). The data is from a US hospital. Performance in your
department may differ.

## 4. Limitations

- Ages under 18 and over 65: the model does not yet use age-specific vital thresholds. Check these
  patients' vitals yourself.
- A missing respiratory rate is read as 0 and gives ESI-1. Enter the respiratory rate whenever you
  can.
- Confidence is hidden after an emergency override; it is not a measure of clinical certainty.

## 5. Human oversight

Review every recommendation in the Coordinator Review dialog. Confirm it, or override it with a
reason. The decision and the reason go to the Audit Trail. If a recommendation looks wrong, use
"Report a problem with this AI recommendation" in the same dialog, and tick "A patient was or may
have been harmed" when that applies.

## 6. Installation

Run the backend and dashboard on the hospital's internal network only, behind the hospital's own
access control. Release 1.0.0 has no sign-in of its own. Use the pinned dependencies in
`development/requirements.txt`.

## 7. Logs

The system writes every assessment, coordinator decision, override and re-triage to the
`audit_logs` table. Keep them as your own record-keeping rules require.
