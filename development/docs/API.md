# PatientTriage.ai API, version 1.0.0

Provider: Nekod Test Labs B.V., Keizersgracht 100, 1015 CW Amsterdam, the Netherlands.
Contact: compliance@nekod-testlabs.example

![CE marking](../../frontend/public/ce-mark.svg)

PatientTriage.ai is a CE marked high-risk AI system under Regulation (EU) 2024/1689
(EU database registration EUDB-HR-2026-0042-PT). Read the instructions for use in
`docs/compliance/instructions-for-use.md` before you connect to this API.

The Flask backend serves every route under `/api` on port 5000. Every ESI level the
API returns is a recommendation from an AI system. A coordinator confirms or
overrides it through `POST /api/coordinator-decision`.

## Routes

| Method | Path | What it does |
| --- | --- | --- |
| POST | `/api/patients` | Register a patient and store the intake data |
| POST | `/api/triage` | Run the CatBoost model and the Safety Engine for a patient |
| GET | `/api/assessments/patient/<patient_id>` | Latest assessment for a patient |
| GET | `/api/assessments/<assessment_id>/explain` | Explanation of an existing assessment |
| POST | `/api/coordinator-decision` | Confirm or override the AI recommendation, with a reason |
| GET | `/api/waiting-queue` | Patients waiting, with their current ESI |
| GET | `/api/in-care` | Patients in care |
| POST | `/api/patients/<patient_id>/vitals` | New vitals, starts a re-triage |
| POST | `/api/event-retriage` | Re-triage after a clinical event |
| POST | `/api/check-retriage` | Check time-based re-triage alerts |
| GET | `/api/retriage-alerts` | Open re-triage alerts |
| POST | `/api/patients/<patient_id>/manual-esi` | Coordinator sets the ESI by hand |
| POST | `/api/patients/<patient_id>/move-to-care` | Move a patient into care |
| POST | `/api/patients/<patient_id>/take-to-care` | Take a patient to care from review |
| POST | `/api/patients/<patient_id>/complete` | Complete the encounter |
| GET | `/api/audit-trail` | Audit trail of assessments, decisions and re-triage |
| POST | `/api/incident-reports` | Report a problem with an AI recommendation |
| GET | `/api/incident-reports` | Problem reports for the provider, possible serious incidents first |
