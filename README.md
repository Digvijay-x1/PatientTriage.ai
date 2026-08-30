# PatientTriage.ai

PatientTriage.ai is a prototype emergency-department coordination and triage-support
platform designed to help healthcare coordinators prioritize patients, identify
potentially deteriorating patients, and maintain a clear, auditable record of triage
decisions.

For this project, the README serves as the primary entry point for the prototype,
including its architecture, model, safety logic, validation approach, workflow, and
prototype limitations.

## Table of contents

- Requirements
- Installation
- Configuration
- Project structure
- Core AI architecture
- Machine-learning model
- Model inputs
- Age-aware vital interpreter
- Safety engine
- Dangerous combinations
- Low-acuity safety logic
- Prior history
- Facility-aware context
- Missing data and reliability
- Re-triage
- Coordinator-in-the-loop
- Audit trail
- Model performance
- Prototype validation
- Demonstrated product workflow
- What makes PatientTriage.ai different
- Regulatory and safety position
- Core message
- Troubleshooting
- FAQ
- Maintainers

---

## Tech Stack

### Backend
- Python
- Flask
- SQLAlchemy
- SQLite
- Scikit-learn
- Pandas
- Joblib

### Frontend
- React
- TypeScript
- Tailwind CSS

---

## Requirements

PatientTriage.ai is a prototype application with a machine-learning component,
backend/integration logic, and a frontend. The exact runtime dependencies should be
installed from the dependency files included with the project.

The prototype also requires the frozen CatBoost model artifact and its associated
vital-threshold configuration to be available at runtime.

No clinical deployment requirements are implied by this prototype README. Any
production deployment would require additional clinical, security, privacy,
infrastructure, regulatory, and institutional requirements.

---

## Project Structure

```text
PatientTriage/
├── development/
│   ├── models/
│   ├── routes/
│   ├── services/
│   │   ├── vital_interpreter.py
│   ├── instances/
│   │   ├── db
│   ├── ml/
│   │   ├── catboost_esi_model_v2.joblib
│   │   ├── vitals_thresholds.json
│   │   ├── history_context.py
│   │   └── audit_log.py
│   └── app.py
│
├── frontend/
│   ├── src/
│   └── package.json
│
└── README.md
```

---

## Installation

## Setup

### Backend

```bash
cd backend
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

Linux/macOS:

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Set the Gemini API key according to the configuration used by `GeminiExplanationService`.

Start Flask:

```bash
python app.py
```

Backend:

`http://127.0.0.1:5000`

### Frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the URL shown by Vite, usually:

`http://localhost:5173`

---

## Running the Demo

1. Register a patient.
2. Run initial triage.
3. Review the ML ESI recommendation.
4. Confirm or override the recommendation.
5. Monitor the patient in the Waiting Queue.
6. Update vitals to trigger re-triage.
7. Review the new AI recommendation and safety flags.
8. Move the patient to In Care when required.
9. Mark the patient as completed.
10. Review decisions in the Audit Trail.

---

## Configuration

The prototype configuration includes the model artifact, vital-threshold
configuration, backend services, frontend application, patient-history context,
and audit logging.

The age-aware Vital Interpreter uses its configured thresholds to distinguish
pediatric, adult, and geriatric interpretation.

The CatBoost model is intentionally kept frozen. Deployment-context features such
as history and facility context are handled outside the frozen model.



## 2. The Core AI Architecture

PatientTriage.ai deliberately separates machine learning from safety and clinical context.

```text
                    PATIENT INTAKE
                         │
                         ▼
              ┌─────────────────────┐
              │    CATBOOST MODEL    │
              │                     │
              │  Frozen / tested    │
              │  ESI prediction     │
              │  ESI probabilities  │
              └──────────┬──────────┘
                         │
                         ▼
                  ML ESI + PROBS
                         │
          ┌──────────────
          │              │             
          ▼              ▼             
     Vital Safety    Patient History   
     Interpreter       Context          
          │              │             
          ▼              ▼            
    Critical/urgent   Relevant risk  
       flags           signals        
          │              │            
          └──────────────┼
                         ▼
                 ┌───────────────┐
                 │ SAFETY ENGINE │
                 │               │
                 │ Emergency?    │
                 │ Dangerous     │
                 │ combinations? │
                 │ Low acuity?   │
                 │ Missing data? │
                 └───────┬───────┘
                         ▼
                    FINAL ESI
                         │
                         ▼
                COORDINATOR DASHBOARD
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
        WAITING QUEUE          NEEDS ATTENTION
                                      │
                                      ▼
                                   RE-TRIAGE
                                      │
                                      ▼
                             COORDINATOR REVIEW
                                      │
                              Confirm / Override
                                      │
                                      ▼
                                AUDIT TRAIL
```

The key design principle is that **the ML model, Vital Interpreter, history context, facility context, and Safety Engine remain separate and explainable**.

---

## 3. Machine-Learning Model

The core prediction model is a **frozen, regression-tested CatBoost model**.

```text
catboost_esi_model_v2.joblib
```

It predicts the Emergency Severity Index across all five levels:

```text
ESI-1
ESI-2
ESI-3
ESI-4
ESI-5
```

The model produces:

- Raw ESI prediction
- Confidence
- Probability distribution across all ESI levels

The model itself is intentionally kept frozen so that deployment-context features do not silently alter its learned behavior.

---

## 4. Model Inputs

The verified CatBoost integration schema contains these 12 inputs:

```text
temperature
heartrate
resprate
o2sat
sbp
dbp
pain
gender
breathing
responsiveness
distress_level
chiefcomplaint
```

The broader system also collects **age** because age is essential to the age-aware Vital Interpreter and pediatric/geriatric safety interpretation.

Patient history and facility information are handled by separate context layers rather than being injected into the frozen CatBoost model.

---

## 5. Age-Aware Vital Interpreter

PatientTriage.ai does not interpret every patient's vital signs using one generic adult threshold.

The Vital Interpreter distinguishes:

- Pediatric patients
- Adult patients
- Geriatric patients

It evaluates available vital signs using the appropriate age-specific thresholds.

It produces:

```text
Age group
Vital status
Critical flags
Urgent flags
Vital reasoning
```

For example:

```text
Temperature → Normal / Urgent / Critical
Heart rate → Normal / Urgent / Critical
Respiratory rate → Normal / Urgent / Critical
SpO₂ → Normal / Urgent / Critical
Blood pressure → Normal / Urgent / Critical
Pain → Normal / Urgent / Critical
```

Pediatric blood pressure is separately interpreted using pediatric-specific logic.

Importantly:

> A critical or urgent vital flag is a **safety signal**, not an automatic ESI-1 decision.

---

## 6. Safety Engine

The Safety Engine sits on top of the ML prediction.

It answers a different question from the CatBoost model:

> “Does the patient's overall presentation require a safety adjustment?”

The system distinguishes between:

```text
NORMAL
     ↓
URGENT
     ↓
CRITICAL
     ↓
IMMEDIATE EMERGENCY
```

These categories are deliberately not treated as equivalent.

### ESI-1

ESI-1 is reserved for an obvious immediate life-threatening emergency.

Examples include:

- Unresponsive/unconscious patient
- Not breathing
- Cardiac arrest/no pulse
- Severe respiratory compromise with appropriate clinical context
- Profound hypoxia with concerning clinical context
- Severe physiologic collapse
- Other explicit life-threatening presentations

A single `critical` flag does **not** automatically force ESI-1.

For an emergency override:

```text
Final ESI: 1
Emergency override: YES
Confidence: HIDDEN
```

This prevents an ML probability from being presented as meaningful after the system has made a deterministic emergency safety decision.

The system further recommends the coordinator to take the patient to care.

---

## 7. Dangerous Combinations

The Safety Engine considers combinations of abnormal findings rather than treating every abnormality independently.

For example:

```text
HR 140
SpO₂ 84%
RR 34
SBP 86
```

is substantially more concerning than an isolated abnormal pain score.

The system therefore uses:

- Critical physiologic findings
- Multiple critical findings
- Clusters of urgent findings
- Clinical context
- Breathing status
- Responsiveness
- Distress
- Complaint context

to determine whether escalation is warranted.

---

## 8. Low-Acuity Safety Logic

The system also addresses the opposite failure mode: unnecessarily high ML acuity for clearly stable patients.

It does **not** use:

```text
if stable:
    ESI = 4
```

Instead, a narrow low-acuity profile can adjust an ML prediction only when the complete presentation supports low acuity.

The profile considers factors such as:

- No immediate emergency
- No critical physiologic combination
- No concerning urgent cluster
- Alert responsiveness
- Normal breathing
- Low distress
- Low pain
- Age-appropriate vital interpretation
- Low-acuity complaint
- Sufficient data completeness

This allows cases such as a stable patient with a mild complaint to reach an appropriate low-acuity level without blindly overriding the model.

The Vital Interpreter's underlying signal is still retained and displayed.

---

## 9. Prior History

PatientTriage.ai does not treat every patient as an isolated encounter.

When prior records are available, the system can incorporate relevant history context.

For example:

```text
Known cardiac history
        +
Current chest-pain complaint
        ↓
Relevant history-risk signal
        ↓
Coordinator attention
```

History alone does not automatically lower or raise ESI.

Instead, the history layer identifies clinically relevant combinations that should inform the coordinator's assessment.

This is especially useful for returning patients who have substantially more information available than a first-time patient.

---

## 10. Facility-Aware Context

Different healthcare facilities have different capabilities.

PatientTriage.ai therefore includes a facility-context layer that can consider:

- Facility type
- Current ESI
- Complaint/context

and recommend a transfer when appropriate.

Importantly:

> Facility capability does not change the patient's ESI.

A patient's clinical acuity remains the same whether they are in a rural emergency department, community facility, or larger trauma center.

---

## 11. Missing Data and Reliability

Emergency-department intake data can be incomplete.

PatientTriage.ai is designed not to crash when information is missing.

The system explicitly reports:

```text
Data completeness
Missing fields
Decision reliability
Clinician review required
```

For example:

```text
Data completeness: 16.7%
Decision reliability: LOW
Clinician review: REQUIRED
```

This prevents ML confidence from being confused with overall clinical certainty.

The model probability remains available for transparency, but incomplete patient information automatically increases the need for human review.

---

## 12. Re-Triage

PatientTriage.ai is not limited to the first triage decision.

Patients can remain in the waiting queue while their condition changes.

The system supports:

```text
Initial triage
      ↓
Waiting Queue
      ↓
Vitals change
      ↓
Re-triage
      ↓
Updated AI recommendation
      ↓
Coordinator review
      ↓
Confirm / Override
```

This addresses a major emergency-department problem:

> A patient who was stable at intake may not remain stable while waiting.

---

## 13. Coordinator-in-the-Loop

The system is intentionally not autonomous.

The coordinator can:

- Review the recommendation
- Review history signals
- Review transfer recommendations
- Confirm the ESI
- Override the recommendation
- Provide an override reason
- Move patients through the workflow

The AI therefore functions as an **assistive decision-support layer**, while responsibility for the final operational decision remains with the appropriate healthcare professional.

---

## 14. Audit Trail

Every important decision can be traced.

The audit trail records:

- AI recommendations
- Safety decisions
- Coordinator confirmations
- Overrides
- Who made the change
- Why the change was made

This creates an auditable history of how the triage recommendation evolved.

That is particularly important when a patient's condition changes and the original recommendation is no longer appropriate.

---

## 15. Model Performance

The current evaluation on MIMIC-IV Demo test data reports:

| Metric | Result |
|---|---:|
| Accuracy | **92.27%** |
| Under-triage | **2.90%** |
| Severe under-triage | **0.00%** |
| Over-triage | **4.83%** |
| Severe over-triage | **0.97%** |
| MAE | **0.087** |
| Within ±1 ESI | **99.03%** |
| ESI-1 recall | **88.89%** |
| ESI-2 recall | **95.88%** |
| ESI-3 recall | **91.11%** |

The evaluation specifically emphasizes safety because under-triage can be more consequential than ordinary over-triage.

The reported severe under-triage rate is **0.00%** on this evaluation.

---

## 16. Prototype Validation

The system is tested against diverse edge cases rather than only average patients.

The validation set includes:

- Stable adults
- Mild complaints
- Chest pain with stable vitals
- Immediate emergencies
- Unresponsive patients
- Stable pediatric patients
- Severe pediatric presentations
- Pediatric respiratory illness
- Stable geriatric patients
- Geriatric fever
- Geriatric confusion
- Dizziness/ambiguous complaints
- Dangerous vitals with under-reported pain
- Conflicting complaint and vital information
- First-time/limited-history patients
- Missing one vital
- Multiple missing vitals
- All vitals missing
- Complaint-only cases
- Almost entirely missing-data cases
- Additional stable pediatric cases

The validation deliberately checks that all five ESI levels remain reachable and that low-acuity patients are not automatically escalated merely because of age or an isolated warning signal.

---

## 18. The Demonstrated Product Workflow

A coordinator can:

1. Register a patient.
2. Enter current patient information and available history.
3. Run initial triage.
4. Review the AI recommendation.
5. Review relevant history context.
6. Review any facility transfer recommendation.
7. Confirm or override the recommendation.
8. Place the patient in the Waiting Queue.
9. Monitor the patient.
10. Update vitals when the condition changes.
11. Trigger re-triage.
12. Review the updated recommendation.
13. Move the patient into care.
14. Complete the encounter.
15. Review the audit trail.

---

## 18. What Makes PatientTriage.ai Different

PatientTriage.ai is not simply:

```text
Patient → ML model → ESI
```

It is:

```text
Patient information
       ↓
ML prediction
       +
Age-aware vital interpretation
       +
Prior history
       ↓
Safety Engine
       ↓
Final ESI
       ↓
Human coordinator
       ↓
Re-triage when necessary
       ↓
Auditable decision history
```

This architecture allows the system to combine the strengths of machine learning with explicit safety logic, contextual information, and human oversight.

---

## 19. Regulatory and Safety Position

PatientTriage.ai is currently an **academic/hackathon prototype**, not a validated medical device.

It should not be presented as a replacement for licensed clinical judgment.

For demonstration purposes, the system emphasizes:

- Human-in-the-loop review
- Explainability
- Auditability
- Conservative emergency safety logic
- Explicit missing-data handling
- Separation of prediction and safety decisions
- Re-triage when patient conditions change

Any real-world deployment would require appropriate clinical validation, regulatory assessment, privacy/security controls, institutional governance, and jurisdiction-specific compliance before clinical use.

---

## 20. Core Message

> **PatientTriage.ai combines machine learning, age-aware vital interpretation, patient history, facility context, safety logic, continuous re-triage, and human oversight into one auditable emergency-department workflow.**

The goal is not to replace clinicians.

The goal is to help them **identify risk faster, understand why a patient was flagged, recognize deterioration while patients are waiting, and make better-informed triage decisions with a traceable record of what happened.**

## Troubleshooting

If the prototype does not produce a prediction:

- Confirm that the required model artifact is available.
- Confirm that the vital-threshold configuration is available.
- Check that all required runtime dependencies are installed.
- Check the backend/application logs for the underlying error.
- Verify that the frontend is sending the expected input fields and values.

If a patient has incomplete data, review the reported data completeness,
decision reliability, missing fields, and clinician-review requirement rather than
treating model confidence as clinical certainty.

If a safety decision differs from the raw ML prediction, review the Vital
Interpreter output and Safety Engine reasoning. The architecture intentionally
keeps these decision sources separate.

## FAQ

**Q: Does a critical vital flag automatically mean ESI-1?**

**A:** No. A critical or urgent vital flag is a safety signal. ESI-1 is reserved
for an obvious immediate life-threatening emergency under the prototype's safety
logic.

**Q: Does the system replace a clinician?**

**A:** No. PatientTriage.ai is decision support and includes coordinator review
and override.

**Q: Does patient history directly change the frozen CatBoost model?**

**A:** No. Relevant history is handled as a separate context layer. Later on, we 
plan to integrate the history and retrain the model, so the model can be updated 
with real data and improve it's real-time efficiency.

**Q: Can the system re-triage a patient?**

**A:** Yes. The prototype supports re-triage when patient conditions change.

**Q: Is PatientTriage.ai clinically validated?**

**A:** No. It is an academic/hackathon prototype and is not a validated medical
device or a substitute for licensed clinical judgment.

## Maintainers

- Team Riwi
- Team Leader: Kavya Mahajan, IIT Patna
- Team Member: Riddhi Rajani, IIT Patna

