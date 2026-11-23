# Serious incident reporting procedure: PatientTriage.ai

| | |
| --- | --- |
| Provider | Nekod Test Labs B.V. |
| Basis | Article 73 of Regulation (EU) 2024/1689; QMS manual, section 11 |
| Owner | Quality and Regulatory Lead (deputy: Managing Director) |
| Approved | 2026-06-04 |

## What counts

A serious incident is an incident or malfunction of PatientTriage.ai that directly or indirectly
leads to the death of a person or serious harm to a person's health, a serious and irreversible
disruption of critical infrastructure, an infringement of obligations under Union law intended to
protect fundamental rights, or serious harm to property or the environment (Article 3(49)).

For this system the most likely case is a patient harmed because a recommendation placed them too
low in the queue (risks R1, R2 and R6 in `risk-management.md`).

## How the provider notices one

| Channel | Where |
| --- | --- |
| Coordinator problem report from the review dialog. A report with "A patient was or may have been harmed" ticked is stored with `possible_serious_incident` set and writes a `POSSIBLE SERIOUS INCIDENT` warning to the server log | `frontend/src/components/ReportProblem.tsx`, `development/routes/incident_reports.py` |
| Review queue of reports, possible serious incidents first | `GET /api/incident-reports?serious=true` |
| Deployer contact by email | compliance@nekod-testlabs.example |
| Quarterly review of overrides in the audit trail | QMS manual, section 10 |

## Steps

| Step | Who | Time |
| --- | --- | --- |
| 1. Read every report flagged as a possible serious incident and open an incident file | Quality and Regulatory Lead | Within 1 working day of the report |
| 2. With the Clinical Safety Officer and the deployer, decide whether there is a causal link between the system and the incident, or a reasonable likelihood of one | Quality and Regulatory Lead | As fast as possible |
| 3. Report to the market surveillance authority of the Member State where the incident happened, and tell the deployer | Quality and Regulatory Lead | See the time limits below |
| 4. Investigate, update the risk register, decide corrective action. Do not change the system in a way that could affect the evaluation of the cause before the authority is informed | Clinical ML Lead | Starts at once |
| 5. Send follow-up and final reports to the authority; close the incident file | Quality and Regulatory Lead | When the investigation ends |

## Time limits (Article 73(2) to (4))

The report goes to the authority immediately after the causal link or its reasonable likelihood is
established, and never later than:

- **15 days** after the provider becomes aware of the serious incident;
- **10 days** if a person may have died;
- **2 days** for a widespread infringement or a serious and irreversible disruption of critical
  infrastructure.

If a complete report is not possible in time, an initial report is sent first and completed later
(Article 73(5)).

## Records

Each incident file holds the report, the assessment of causality, the report sent to the authority
with its date, the correspondence and the corrective action. Files are kept for 10 years
(`documentation-retention.md`).
