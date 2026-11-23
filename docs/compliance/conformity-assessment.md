# Conformity assessment record: PatientTriage.ai 1.0.0

| | |
| --- | --- |
| Provider | Nekod Test Labs B.V., Keizersgracht 100, 1015 CW Amsterdam, the Netherlands |
| System | PatientTriage.ai 1.0.0, model `catboost_esi_model_v3.joblib` (SHA-256 `b18fa75c2acf6cd294a9f192dc01235221a240ab5205b0fa53a22437d2d41475`) |
| Procedure | Internal control, Article 43(2) and Annex VI. No notified body is involved. |
| Started | 2026-05-25 |
| Completed | 2026-06-05 |
| Result | Conforms |
| First production release | 2026-06-15 (`CHANGELOG.md`) |

## Why internal control

PatientTriage.ai is high-risk under Annex III point 5(d) (emergency healthcare patient triage).
For systems in Annex III points 2 to 8, Article 43(2) sets the internal control procedure of
Annex VI.

## Annex VI checklist

| Annex VI step | Checked | Evidence | Result |
| --- | --- | --- | --- |
| 2. The quality management system complies with Article 17 | Each point of Article 17(1) has a section in the QMS manual with an owner | `quality-management-system.md` | Conforms |
| 3. The technical documentation shows compliance with Chapter III, Section 2 | Each article 8 to 15 mapped to evidence | `README.md` in this folder, `technical-documentation.md` | Conforms |
| 4. Design, development and post-market monitoring are consistent with the technical documentation | Model hash in `ci` matches the documented artifact; Safety Engine rules in `predict.py` match the README; release validation met the targets; problem-report route in place | `.github/workflows/ci.yml`, `development/tests/test_safety_engine.py`, `development/routes/incident_reports.py` | Conforms |

## Section 2 requirements

| Article | Finding | Result |
| --- | --- | --- |
| 9 Risk management | Register with review log; residual risk accepted 2026-06-04, with R4, R7 and R11 open until 1.1.0 | Conforms |
| 10 Data and data governance | Data source, labelling and filtration documented (QMS manual, section 8). Population difference handled as risk R8 | Conforms |
| 11 Technical documentation | Present and complete for Annex IV | Conforms |
| 12 Record-keeping | Assessments, decisions and re-triage written to `audit_logs` | Conforms |
| 13 Transparency and instructions | Instructions for use; AI system notice in the dashboard | Conforms |
| 14 Human oversight | Coordinator confirms or overrides every recommendation with a reason | Conforms |
| 15 Accuracy, robustness, cybersecurity | Release targets met; input validation; no API authentication, controlled by the deployment condition in the instructions for use (risk R11) | Conforms, with R11 open |

## Sign-off

| Role | Date |
| --- | --- |
| Assessed by: Quality and Regulatory Lead | 2026-06-05 |
| Clinical review: Clinical Safety Officer | 2026-06-05 |
| Approved: Managing Director | 2026-06-05 |

A new assessment is required before a substantial modification is placed on the market
(QMS manual, section 4).
