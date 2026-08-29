import os
import json
import importlib

from dotenv import load_dotenv


genai = importlib.import_module("google.genai")
types = importlib.import_module("google.genai.types")


# Load .env
load_dotenv()


class GeminiExplanationService:

    def __init__(self):

        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY not found in .env"
            )

        self.client = genai.Client(
            api_key=api_key
        )

        self.model = "gemini-3.7-flash"

    def explain_triage(
        self,
        patient,
        assessment
    ):

        prompt = f"""
You are an explanation assistant for a prototype emergency
department triage support system.

A separate machine-learning model has already made the triage
prediction. Your role is ONLY to explain that prediction in
clear, natural language for a healthcare coordinator.

Do NOT make a new triage decision.

The ML model's predicted ESI, confidence, probability distribution,
and the patient's clinical data are provided below.

PATIENT DATA:
{json.dumps(patient, indent=2)}

ML AND SAFETY ENGINE RESULT:
{json.dumps(assessment, indent=2)}

Your task is to explain WHY the ML model arrived at its existing
prediction using the information provided.

STRICT RULES:

1. Never change, recalculate, or suggest another ESI level.
2. The predicted ESI MUST be taken directly from "esi_level" or
   "ml_esi" in the ML AND SAFETY ENGINE RESULT.
3. The confidence MUST be taken directly from "confidence".
4. Do not diagnose the patient.
5. Do not invent symptoms, history, vitals, or observations.
6. Do not assume that a finding influenced the model unless the
   supplied model result provides evidence for that.
7. Use the patient's actual values when explaining the prediction.
   For example, mention SpO₂, heart rate, blood pressure,
   temperature, respiratory rate, age, sex, or complaint when
   they are actually present and relevant.
8. Give greater attention to findings explicitly marked as
   critical or urgent by the safety engine.
9. The safety engine and ML model are separate components.
   Clearly distinguish between:
   - what the ML model predicted
   - what the safety engine flagged
10. Do not claim that the patient is safe or stable.
11. Do not recommend treatment.
12. Do not override or second-guess the ML prediction.
13. Do not describe internal chain-of-thought or hidden reasoning.
14. Keep the explanation concise and natural. Write as a coordinator
    would expect to read it during a busy clinical workflow.

Use the probability distribution only when it helps explain the
model's confidence. Do not interpret probabilities as clinical
risk percentages.

Return ONLY the following:

Predicted ESI: ESI-[exact ML prediction]

Confidence: [exact confidence percentage and confidence band]

Why this prediction:
[2-4 natural-language sentences explaining the important patient
findings that are relevant to understanding the ML prediction.
Use actual values from the patient data.]

Safety findings:
[Briefly state any critical or urgent findings from the safety
engine. If none are present, say "No critical or urgent vital
findings were flagged by the safety engine."]

Coordinator review:
[State whether clinical/coordinator review is flagged by the
safety engine. Do not add your own clinical recommendation.]

Do not add any other sections.
"""

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=300
            )
        )

        return response.text