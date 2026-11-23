# Quality management system: PatientTriage.ai

| | |
| --- | --- |
| Provider | Nekod Test Labs B.V., Keizersgracht 100, 1015 CW Amsterdam, the Netherlands |
| System | PatientTriage.ai, release 1.0.0 |
| Document | QMS manual, version 1.2 |
| Owner | Quality and Regulatory Lead |
| Approved by | Managing Director, 2026-06-04 |
| First adopted | 2026-01-12 |
| Next review | 2027-01-12, or earlier after a significant change |

This manual is the quality management system (QMS) of Nekod Test Labs B.V. for PatientTriage.ai,
as required by Article 17(1) of Regulation (EU) 2024/1689. Each section below is one point of
Article 17(1) and says the policy, the procedure and who carries it out. The QMS documents are the
files in `docs/compliance/`, kept in this repository.

## 1. Scope

PatientTriage.ai recommends an Emergency Severity Index (ESI) level for patients arriving at an
emergency department. A frozen CatBoost model (`development/ml/catboost_esi_model_v3.joblib`) gives
the ESI and its probabilities, and a rule-based Safety Engine (`development/ml/predict.py`) adjusts
it for emergencies, high-risk presentations and missing data. A coordinator confirms or overrides
every recommendation in the dashboard (`frontend/`).

The system is an emergency healthcare patient triage system, high-risk under Article 6(2) and
Annex III point 5(d). Nekod Test Labs B.V. is its provider.

## 2. Document control

- QMS documents are Markdown files in `docs/compliance/`. A change to them is a pull request,
  approved by the Quality and Regulatory Lead (code owner of `/docs/compliance/`, see
  `.github/CODEOWNERS`).
- Each document states its version, owner and approval date at the top. Git history keeps every
  earlier version.
- The Quality and Regulatory Lead reviews this manual once a year and after every significant change.

## 3. Regulatory compliance strategy (Art. 17(1)(a))

| Obligation | How it is met | Record |
| --- | --- | --- |
| Classification | High-risk, Annex III point 5(d). Reviewed at every significant change. | `technical-documentation.md`, section 1 |
| Conformity assessment | Internal control (Article 43(2), Annex VI), completed before each release that is placed on the market | `conformity-assessment.md` |
| EU declaration of conformity | Drawn up after the conformity assessment, signed by the Managing Director | `eu-declaration-of-conformity.md` |
| CE marking | In the dashboard footer and on the accompanying documents | `frontend/src/components/ProviderFooter.tsx`, `instructions-for-use.md` |
| Registration | EU database (Article 49(1)) before placing on the market | `eu-database-registration.md` |
| Documentation retention | 10 years (Article 18) | `documentation-retention.md` |
| Requests from authorities | Compliance file and procedure | `README.md` in this folder |

## 4. Change management (Art. 17(1)(a))

Every modification to PatientTriage.ai follows these steps.

1. **Propose.** The author opens a pull request with the template in `.github/pull_request_template.md`
   and classifies the change:
   - *Minor*: no effect on the model, the Safety Engine, the thresholds in
     `development/ml/vitals_thresholds.json` or the intended purpose.
   - *Significant*: any change to those. A new model artifact, a change to `predict.py` or to a
     threshold is always significant.
2. **Review.** The code owners of every changed path review it (`.github/CODEOWNERS`). The branch
   protection in `.github/settings.yml` blocks the merge until one code owner approves and the `ci`
   checks pass.
3. **Assess.** For a significant change the Clinical ML Lead updates the risk register
   (`risk-management.md`) and reruns the release validation (section 6).
4. **Approve.** The Quality and Regulatory Lead approves a significant change in the pull request
   and decides whether it is a substantial modification under Article 3(23). A substantial
   modification needs a new conformity assessment, a new declaration and an update of the EU
   database entry before release.
5. **Record.** The change goes into `CHANGELOG.md` with its release.

## 5. Design and development control (Art. 17(1)(b) and (c))

- **Design inputs**: the intended purpose (section 1), the ESI Implementation Handbook (section 7)
  and the risk register.
- **Design decisions** are recorded as decision records in `docs/compliance/decisions/`.
- **Design verification**: code review by code owners on every pull request, the tests in
  `development/tests/`, and the release validation in section 6.
- **Development quality control**: dependencies pinned (section 13), the model artifact checked
  against its SHA-256 in continuous integration, lint and build of the frontend on every change.
- **Release**: the Clinical ML Lead and the Quality and Regulatory Lead sign off the release
  checklist in section 6 before the version is placed on the market.

## 6. Examination, test and validation (Art. 17(1)(d))

| When | What | How often | Who |
| --- | --- | --- | --- |
| Before development | Review of the change against the intended purpose and the risk register | Every significant change | Clinical ML Lead |
| During development | `development/tests/` and frontend lint and build in `.github/workflows/ci.yml` | Every push and pull request, and every Monday at 06:00 UTC | Automatic |
| Before release | Release validation on the held-out MIMIC-IV-ED Demo test split, with the targets below, and the edge-case set in the README (section 16) | Every release | Clinical ML Lead |
| After release | Re-evaluation against coordinator-confirmed ESI levels from the audit trail | Every quarter | Clinical ML Lead |

Release targets: severe under-triage 0%, under-triage at most 5%, ESI-1 recall at least 85%,
within one ESI level at least 97%. Release 1.0.0 met them (README, section 15).

Release checklist: tests pass in `ci`; release validation meets the targets; risk register
reviewed; `CHANGELOG.md` updated; for a substantial modification, conformity assessment,
declaration and EU database entry updated.

## 7. Technical specifications and standards (Art. 17(1)(e))

No harmonised standard for Regulation (EU) 2024/1689 was cited in the Official Journal when this
manual was approved. PatientTriage.ai follows these specifications instead, and the compliance file
(`README.md` in this folder) records for each requirement of Chapter III, Section 2 the evidence
used to meet it.

| Specification | Used for |
| --- | --- |
| Regulation (EU) 2024/1689, Chapter III, Section 2 | The requirements themselves |
| ISO/IEC 42001:2023 | Structure of this QMS (not certified) |
| ISO/IEC 23894:2023 | Risk management method (`risk-management.md`) |
| Emergency Severity Index Implementation Handbook, version 4 | Definition of ESI levels 1 to 5 and of the ESI-1 criteria in the Safety Engine |
| WCAG 2.1, level AA | AI system notice and legal notice in the dashboard |

## 8. Data management (Art. 17(1)(f))

- **Acquisition**: training and test data come from the MIMIC-IV-ED Demo dataset (PhysioNet). No
  data from deployers is used for training. The model is frozen; new data never changes it outside
  the change procedure.
- **Labelling**: the ESI label is the triage acuity recorded in the dataset. Rows without acuity
  are dropped.
- **Filtration and preparation**: only the 12 inputs listed in the README (section 4) are kept.
  Out-of-range values are rejected at prediction time by `_validate_patient` in
  `development/ml/predict.py`.
- **Storage**: the dataset stays in the provider's research environment under the PhysioNet data
  use agreement. Only the trained artifact is in this repository.
- **Patient data in use**: intake data, assessments, coordinator decisions and the audit trail are
  stored in the deployer's database (`development/models/`). The deployer decides how long they are
  kept. The provider receives only the problem reports sent through `POST /api/incident-reports`.
- **Vital thresholds**: `development/ml/vitals_thresholds.json` changes only through the change
  procedure in section 4.

## 9. Risk management (Art. 17(1)(g))

The risk management system of Article 9 is part of this QMS. It is described, with the risk
register and its review log, in `risk-management.md`.

## 10. Post-market monitoring (Art. 17(1)(h))

Coordinators report problems with an AI recommendation from the review dialog
(`frontend/src/components/ReportProblem.tsx`). The Clinical ML Lead reviews the reports, the
override rate in the audit trail and the quarterly re-evaluation (section 6), and records the
result in the review log of `risk-management.md`.

## 11. Serious incident reporting (Art. 17(1)(i))

Possible serious incidents are handled under `serious-incident-reporting.md`.

## 12. Communication (Art. 17(1)(j))

| Party | Handled by | Channel |
| --- | --- | --- |
| National competent authorities and market surveillance authorities | Quality and Regulatory Lead | compliance@nekod-testlabs.example; procedure in `README.md` in this folder |
| Notified bodies | Quality and Regulatory Lead | None involved: the conformity assessment is internal control |
| Deployers (hospitals) | Customer Success Lead | Named contact per hospital in the service agreement; release notes from `CHANGELOG.md` |
| Coordinators using the system | Customer Success Lead | In-app problem report; instructions for use |
| Suppliers (hosting, libraries) | Clinical ML Lead | Supplier list in section 13 |
| Other interested parties | Quality and Regulatory Lead | compliance@nekod-testlabs.example |

Every message to or from an authority is filed under section 13.

## 13. Record-keeping (Art. 17(1)(k))

- Records kept: QMS documents, technical documentation, conformity assessment records, the
  declaration of conformity, the EU database registration, risk register and review log,
  release validation results, problem reports and serious incident files, and correspondence with
  authorities.
- Documents live in this Git repository, where history is preserved and `main` is protected from
  rewrites (`.github/settings.yml`). Correspondence and incident files are kept in the provider's
  document archive with a retention lock.
- Retention periods are in `documentation-retention.md`.

## 14. Resource management and security of supply (Art. 17(1)(l))

- **People**: the roles in section 15 are filled before a release is placed on the market. The
  Managing Director assigns a deputy for each role.
- **Model**: trained and kept by the provider; no external model supplier. The released artifact is
  `catboost_esi_model_v3.joblib`, SHA-256
  `b18fa75c2acf6cd294a9f192dc01235221a240ab5205b0fa53a22437d2d41475`, checked in `ci`.
- **Dependencies**: Python dependencies pinned to exact versions in `development/requirements.txt`,
  with CatBoost pinned to 1.2.8, the version the model was saved with. Frontend dependencies pinned
  by `frontend/package-lock.json`.
- **Fallback supplier**: if the CatBoost library can no longer be obtained or maintained, the
  fallback is scikit-learn's `HistGradientBoostingClassifier`, retrained on the same data under the
  change procedure as a significant change. Wheels of the pinned CatBoost version are mirrored in the
  provider's package cache so a build never depends on the public index alone.
- **Hosting**: PatientTriage.ai runs on the deployer's own servers; the provider supplies no hosted
  service.

## 15. Accountability (Art. 17(1)(m))

| Role | Responsible for | Code owner team |
| --- | --- | --- |
| Managing Director | Approves this QMS, accepts residual risk, signs the declaration of conformity | |
| Quality and Regulatory Lead | Runs the QMS, the conformity assessment, registration, serious incident reports and contact with authorities | `@nekod-testlabs/quality-regulatory` |
| Clinical ML Lead | Model, Safety Engine, thresholds, release validation, risk register, post-market review | `@nekod-testlabs/clinical-ml` |
| Clinical Safety Officer (emergency physician) | Clinical review of risks, of the Safety Engine rules and of possible serious incidents | |
| Frontend Lead | Dashboard, AI system notice, legal notice, accessibility | `@nekod-testlabs/frontend` |
| Customer Success Lead | Deployers, training of coordinators, problem reports from hospitals | |

Owners of each part of the code are in `.github/CODEOWNERS`.
