# Compliance file: PatientTriage.ai

Provider: Nekod Test Labs B.V., Keizersgracht 100, 1015 CW Amsterdam, the Netherlands.
Contact for authorities: Quality and Regulatory Lead, compliance@nekod-testlabs.example

This folder is the compliance file for PatientTriage.ai 1.0.0, a high-risk AI system under
Annex III point 5(d). It is what the provider hands to a national competent authority to
demonstrate conformity with Chapter III, Section 2 of Regulation (EU) 2024/1689 (Article 16(k)).

## Documents

| Document | Article |
| --- | --- |
| `quality-management-system.md` | 17 |
| `risk-management.md` | 9 |
| `technical-documentation.md` | 11, Annex IV |
| `instructions-for-use.md` | 13 |
| `conformity-assessment.md` | 43, Annex VI |
| `eu-declaration-of-conformity.md` | 47 |
| `eu-database-registration.md` | 49 |
| `documentation-retention.md` | 18 |
| `serious-incident-reporting.md` | 73 |
| `decisions/` | Design decisions |

## Section 2 requirements and their evidence

| Article | Requirement | Evidence |
| --- | --- | --- |
| 8 | Compliance with Section 2, taking into account the intended purpose | This table; `conformity-assessment.md` |
| 9 | Risk management system | `risk-management.md` |
| 10 | Data and data governance | QMS manual, section 8; `development/ml/predict.py` (`_validate_patient`); risk R8 |
| 11 | Technical documentation | `technical-documentation.md` |
| 12 | Record-keeping (logs) | `development/models/audit_log.py`; writes in `development/routes/triage.py` and `development/routes/coordinator_review.py`; Audit Trail tab in `frontend/src/pages/Dashboard.tsx` |
| 13 | Transparency and instructions for use | `instructions-for-use.md`; AI system notice `frontend/src/components/AiDisclosure.tsx` |
| 14 | Human oversight | Confirm and override in `development/routes/coordinator_review.py` and `frontend/src/components/PatientReview.tsx` |
| 15 | Accuracy, robustness and cybersecurity | README, section 15; `development/tests/test_safety_engine.py`; `.github/workflows/ci.yml`; risks R7 and R11 |

## Requests from authorities

1. A request goes to compliance@nekod-testlabs.example or to the registered address. Whoever receives
   it forwards it to the Quality and Regulatory Lead the same day.
2. The Quality and Regulatory Lead acknowledges it within 2 working days and logs it in the
   authority correspondence register (QMS manual, section 13).
3. The Quality and Regulatory Lead sends the documents from this folder, the logs the provider
   controls, and answers to the authority's questions, in a language the authority understands,
   within the time the authority sets.
4. When the authority asks for access to the logs at a hospital, the Customer Success Lead arranges
   it with the deployer.
5. The Managing Director is informed of every request and signs off the final answer.
