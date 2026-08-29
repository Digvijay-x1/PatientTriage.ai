# PatientTriage.ai

## AI-Assisted Emergency Department Triage Support System

PatientTriage.ai is a prototype emergency department coordination and
triage support system designed to help healthcare coordinators prioritize
patients, identify potentially deteriorating patients, and maintain a
clear audit trail of triage decisions.

The system combines a machine-learning ESI prediction model with a
vital-sign safety engine and a coordinator-facing dashboard.

> IMPORTANT: PatientTriage.ai is a prototype decision-support system.
> It does not replace clinical judgment, diagnosis, or treatment decisions.

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

### AI
- Google Gemini

---

## Project Structure

```text
PatientTriage/
├── development/
│   ├── models/
│   ├── routes/
│   ├── services/
│   ├── ml/
│   │   ├── esi_integrated_model.joblib
│   │   └── vitals_thresholds.json
│   └── app.py
│
├── frontend/
│   ├── src/
│   └── package.json
│
└── README.md
```

---

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

# Problem Statement

Emergency departments can become congested when many patients arrive simultaneously. Initial triage requires healthcare staff to quickly evaluate patients and assign an Emergency Severity Index (ESI) level.

The challenge is that:

- Patient information can be incomplete during initial assessment.
- Vital signs may change while a patient is waiting.
- Patients may deteriorate after their initial triage.
- AI recommendations need human oversight.
- Changes in triage decisions need to be traceable.

PatientTriage.ai addresses these challenges by providing:

1. ML-assisted ESI prediction.
2. Vital-sign safety screening.
3. Re-triage when patient conditions change.
4. Coordinator review and override.
5. Waiting queue management.
6. In-care patient tracking.
7. Audit trail of important clinical decisions.

---

# System Overview

The system follows this workflow:

Patient Intake
      |
      v
Patient Data + Vital Signs
      |
      v
Random Forest ESI Model
      |
      +----------------------+
      |                      |
      v                      v
ESI Prediction         Vital Safety Engine
      |                      |
      |              Critical / Urgent Flags
      |                      |
      +----------+-----------+
                 |
                 v
        Coordinator Dashboard
                 |
        +--------+--------+
        |                 |
        v                 v
   Waiting Queue      Needs Attention
                          |
                          v
                     Re-triage
                          |
              +-----------+-----------+
              |                       |
              v                       v
       Updated Vitals          Condition Worsened
              |                       |
              v                       v
        ML Prediction            Urgent Flag
              |                       |
              +-----------+-----------+
                          |
                          v
                  Coordinator Review
                          |
                 Confirm / Override
                          |
                          v
                    Audit Trail


## Features

- Patient intake and registration
- ESI prediction using a Random Forest ML model
- Age-aware vital-sign safety screening
- Pediatric blood-pressure screening
- ML confidence and probability scores
- Gemini-powered natural-language explanation of ML predictions
- Event-driven re-triage when vitals change
- Urgent escalation when a patient's condition worsens
- Coordinator confirmation and ESI override
- Waiting Queue and Needs Attention panels
- In Care and patient completion workflow
- Clinical decision audit trail

---

## ML Model

The system uses a pre-trained Random Forest model:

`ml/esi_integrated_model.joblib`

### Input Features

- Age
- Sex/Gender
- Chief Complaint
- Temperature
- Heart Rate
- Respiratory Rate
- SpO₂
- Systolic Blood Pressure
- Diastolic Blood Pressure
- Pain

The model outputs:

- ESI level (1–5)
- Prediction confidence
- Probability distribution across ESI levels

---

## Safety Engine

A separate vital-sign safety layer uses:

`ml/vitals_thresholds.json`

It provides:

- Age-aware vital interpretation
- Critical vital flags
- Urgent vital flags
- Pediatric AAP blood-pressure screening
- Automatic coordinator-review flags

The safety engine acts as an additional layer and does not replace the ML prediction.

---

## System Flow

```text
Patient Intake
      ↓
ML ESI Prediction
      ↓
Vital Safety Engine
      ↓
Coordinator Dashboard
      ↓
Waiting Queue / Needs Attention
      ↓
Re-triage if condition changes
      ↓
Coordinator Review
      ↓
Confirm / Override / Take to Care
      ↓
Audit Trail
```

Gemini is used only to explain the existing ML prediction in natural language. It does not determine or modify the ESI level.

---


## Disclaimer

PatientTriage.ai is an academic prototype for demonstrating an AI-assisted emergency department triage workflow. It is not a validated medical device and must not be used as a substitute for qualified clinical judgment.
