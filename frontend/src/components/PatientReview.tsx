import { useEffect, useState, useRef } from "react";
import {
  getPatientAssessment,
  getWaitingQueue,
  submitCoordinatorDecision,
  submitVitalCheck,
  takePatientToCare,
} from "../services/api";
import { getAssessmentExplanation } from "../services/api";
import type { TriageAssessment, EsiLevel, ConfidenceBand } from "../types/patient";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "./ui/dialog";
type PatientReviewProps = {
  patientId: string;
  onClose: () => void;
  onDecisionComplete: () => void;
};

import { useLanguage } from "../context/LanguageContext";
function PatientReview({
  patientId,
  onClose,
  onDecisionComplete,
}: PatientReviewProps) {
  const [assessment, setAssessment] =
    useState<TriageAssessment | null>(null);

  const [currentEsi, setCurrentEsi] = useState<number | null>(null);
  const {t} = useLanguage();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [takingToCare, setTakingToCare] = useState(false);
  const [decision, setDecision] = useState<
    "confirmed" | "override" | null
  >(null);
  const decisionMadeRef = useRef(false);

  const [overrideMode, setOverrideMode] = useState(false);
  const [overrideEsi, setOverrideEsi] = useState("3");
  const [overrideReason, setOverrideReason] = useState("");

  const [showVitalCheck, setShowVitalCheck] = useState(false);

const [vitals, setVitals] = useState({
  spo2: "",
  heart_rate: "",
  bp_systolic: "",
  bp_diastolic: "",
  temperature: "",
  respiratory_rate: "",
});

const [vitalLoading, setVitalLoading] = useState(false);

const [vitalResult, setVitalResult] = useState<{
  previous_vitals: Record<string, number | null>;
  new_vitals: Record<string, number | null>;
  assessment: {
    assessment_id: number;
    esi_level: number;
    confidence: number;
    confidence_band: string;
    reasoning: string[];
  };
} | null>(null);

  useEffect(() => {
  async function loadAssessment() {
    try {
      setLoading(true);
      setError(null);

      const [data, queueData] = await Promise.all([
  getPatientAssessment(Number(patientId)),
  getWaitingQueue(),
]);

if (decisionMadeRef.current) {
  return;
}

setAssessment(data);

const queuePatient = queueData.patients.find(
  (patient) =>
    patient.patient_id === Number(patientId),
);

if (queuePatient) {
  setCurrentEsi(queuePatient.esi_level);
}
    } catch (err) {
      // A decision may have been completed while this
      // request was still running. Ignore that stale error.
      if (decisionMadeRef.current) {
        return;
      }

      console.error(
        "Failed to load patient assessment:",
        err,
      );

      setError(
        err instanceof Error
          ? err.message
          : "Unable to load assessment",
      );
    } finally {
      if (!decisionMadeRef.current) {
        setLoading(false);
      }
    }
  }

  loadAssessment();
}, [patientId]);

  const handleVitalCheck = async () => {
  const patientNumber = Number(patientId);

  try {
    setVitalLoading(true);
    setError(null);

    const result = await submitVitalCheck({
      patient_id: patientNumber,

      vitals: {
        spo2:
          vitals.spo2 !== ""
            ? Number(vitals.spo2)
            : undefined,

        heart_rate:
          vitals.heart_rate !== ""
            ? Number(vitals.heart_rate)
            : undefined,

        bp_systolic:
          vitals.bp_systolic !== ""
            ? Number(vitals.bp_systolic)
            : undefined,

        bp_diastolic:
          vitals.bp_diastolic !== ""
            ? Number(vitals.bp_diastolic)
            : undefined,

        temperature:
          vitals.temperature !== ""
            ? Number(vitals.temperature)
            : undefined,

        respiratory_rate:
          vitals.respiratory_rate !== ""
            ? Number(vitals.respiratory_rate)
            : undefined,
      },
    });

    setVitalResult(result);
    setAssessment({
  success: true,

  assessment_id: result.assessment.assessment_id,

  esi_level: result.assessment.esi_level as EsiLevel,

  confidence: result.assessment.confidence,

  confidence_band:
    result.assessment.confidence_band as ConfidenceBand,

  reasoning: result.assessment.reasoning,

  auto_escalate_for_review:
    result.assessment.auto_escalate_for_review,
});
    setShowVitalCheck(false);
  } catch (err) {
    console.error(
      "Failed to submit vital check:",
      err,
    );

    setError(
      err instanceof Error
        ? err.message
        : "Unable to process vital check",
    );
  } finally {
    setVitalLoading(false);
  }
};

  const handleConfirm = async () => {
  if (!assessment) return;

  try {
    setError(null);

    await submitCoordinatorDecision({
      assessment_id: assessment.assessment_id,
      coordinator_esi_level: assessment.esi_level,
      is_override: false,
      override_reason: "",
    });

    // Tell any in-flight assessment request that this
    // assessment has already been handled.
    decisionMadeRef.current = true;

    setDecision("confirmed");

    // Close + refresh dashboard
    onDecisionComplete();

  } catch (err) {
    console.error(
      "Failed to save coordinator decision:",
      err,
    );

    setError(
      err instanceof Error
        ? err.message
        : "Unable to save coordinator decision",
    );
  }
};

 const handleOverride = async () => {
  if (!assessment || !overrideReason.trim()) return;

  try {
    await submitCoordinatorDecision({
  assessment_id: assessment.assessment_id,
  coordinator_esi_level: Number(
    overrideEsi,
  ) as TriageAssessment["esi_level"],
  is_override: true,
  override_reason: overrideReason.trim(),
});

decisionMadeRef.current = true;

setDecision("override");
setOverrideMode(false);

onDecisionComplete();
  } catch (err) {
    console.error(
      "Failed to save coordinator override:",
      err,
    );

    setError(
      err instanceof Error
        ? err.message
        : "Unable to save coordinator override",
    );
  }
};

  const handleTakeToCare = async () => {
  try {
    setTakingToCare(true);
    setError(null);

    await takePatientToCare(Number(patientId));

    onDecisionComplete();
  } catch (err) {
    console.error(
      "Failed to take patient to care:",
      err,
    );

    setError(
      err instanceof Error
        ? err.message
        : "Unable to take patient to care",
    );
  } finally {
    setTakingToCare(false);
  }
};

 return (
  <Dialog open={true} onOpenChange={onClose}>
    <DialogContent
  className="
    flex
    max-h-[85vh]
    w-[calc(100%-2rem)]
    max-w-2xl
    flex-col
    gap-0
    overflow-hidden
    p-0
  "
>
      {/* ================= HEADER ================= */}

      <DialogHeader className="shrink-0 border-b border-slate-200 px-6 py-5 text-left">
        <DialogTitle className="text-xl font-bold text-slate-900">
          {t("Coordinator Review")}
        </DialogTitle>

        <p className="mt-1 text-sm text-slate-500">
          {t("Patient")} {patientId}
        </p>
      </DialogHeader>

      {/* ================= SCROLLABLE CONTENT ================= */}

      <div className="min-h-0 flex-1 overflow-y-auto">
        <div className="px-6 py-6">

          {/* Loading */}

          {loading && (
            <div className="py-12 text-center">
              <p className="text-sm text-slate-500">
                {t("Loading patient assessment...")}
              </p>
            </div>
          )}

          {/* Error */}

          {!loading && error && (
            <div className="rounded-xl border border-red-200 bg-red-50 p-5">
              <p className="text-sm font-semibold text-red-700">
                {t("Unable to load assessment")}
              </p>

              <p className="mt-1 text-sm text-red-600">
                {error}
              </p>
            </div>
          )}

          {/* Assessment */}

          {!loading && !error && assessment && (
            <>
              {/* ================= PATIENT INFORMATION ================= */}

              <section>
                <h3 className="text-sm font-semibold text-slate-900">
                  {t("Patient Information")}
                </h3>

                <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-4">

                  <Info
                    label={t("Patient ID")}
                    value={patientId}
                  />

                  <Info
  label={t("Review Status")}
  value={
    assessment.auto_escalate_for_review
      ? t("Requires Review")
      : t("No Review Required")
  }
/>

                  <Info
                    label={t("Confidence")}
                    value={`${Math.round(
                      assessment.confidence * 100,
                    )}%`}
                  />

                  <Info
                    label={t("Confidence Band")}
                    value={t(assessment.confidence_band)}
                  />

                </div>
              </section>
              {/* ================= VITAL CHECK ================= */}

              <section className="mt-6">

                {!showVitalCheck && !vitalResult && (
                  <button
                    type="button"
                    onClick={() => setShowVitalCheck(true)}
                    className="w-full rounded-xl border border-blue-200 bg-blue-50 px-4 py-4 text-left transition hover:bg-blue-100"
                  >
                    <p className="text-sm font-semibold text-blue-700">
                      {t("Add Vital Check")}
                    </p>

                    <p className="mt-1 text-xs text-blue-600">
                      {t(
                        "Record new vitals and reassess the patient's condition.",
                      )}
                    </p>
                  </button>
                )}

                {showVitalCheck && (
                  <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">

                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="text-sm font-semibold text-slate-900">
                          {t("New Vital Check")}
                        </h3>

                        <p className="mt-1 text-xs text-slate-500">
                          {t(
                            "Enter the patient's latest measurements.",
                          )}
                        </p>
                      </div>

                      <button
                        type="button"
                        onClick={() => setShowVitalCheck(false)}
                        className="text-sm text-slate-500 hover:text-slate-900"
                      >
                        {t("Cancel")}
                      </button>
                    </div>

                    <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">

                      <VitalInput
                        label={t("SpO₂ (%)")}
                        value={vitals.spo2}
                        onChange={(value) =>
                          setVitals((current) => ({
                            ...current,
                            spo2: value,
                          }))
                        }
                      />

                      <VitalInput
                        label={t("Heart Rate (bpm)")}
                        value={vitals.heart_rate}
                        onChange={(value) =>
                          setVitals((current) => ({
                            ...current,
                            heart_rate: value,
                          }))
                        }
                      />

                      <VitalInput
                        label={t("Systolic BP")}
                        value={vitals.bp_systolic}
                        onChange={(value) =>
                          setVitals((current) => ({
                            ...current,
                            bp_systolic: value,
                          }))
                        }
                      />

                      <VitalInput
                        label={t("Diastolic BP")}
                        value={vitals.bp_diastolic}
                        onChange={(value) =>
                          setVitals((current) => ({
                            ...current,
                            bp_diastolic: value,
                          }))
                        }
                      />

                      <VitalInput
                        label={t("Temperature (°C)")}
                        value={vitals.temperature}
                        onChange={(value) =>
                          setVitals((current) => ({
                            ...current,
                            temperature: value,
                          }))
                        }
                      />

                      <VitalInput
                        label={t("Respiratory Rate")}
                        value={vitals.respiratory_rate}
                        onChange={(value) =>
                          setVitals((current) => ({
                            ...current,
                            respiratory_rate: value,
                          }))
                        }
                      />

                    </div>

                    <button
                      type="button"
                      disabled={vitalLoading}
                      onClick={handleVitalCheck}
                      className="mt-5 w-full rounded-lg bg-slate-900 px-4 py-3 text-sm font-semibold text-white transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      {vitalLoading
                        ? t("Running re-triage...")
                        : t("Run Re-triage")}
                    </button>

                  </div>
                )}

                {/* Vital Result */}

                {vitalResult && (
                  <div className="rounded-xl border border-blue-200 bg-blue-50 p-5">

                    <h3 className="text-sm font-semibold text-blue-800">
                      {t("Vital Change Detected")}
                    </h3>

                    <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">

                      <VitalComparison
                        label={t("SpO₂")}
                        previous={
                          vitalResult.previous_vitals.spo2
                        }
                        current={
                          vitalResult.new_vitals.spo2
                        }
                        suffix="%"
                      />

                      <VitalComparison
                        label={t("Heart Rate")}
                        previous={
                          vitalResult.previous_vitals.heart_rate
                        }
                        current={
                          vitalResult.new_vitals.heart_rate
                        }
                        suffix=" bpm"
                      />

                      <VitalComparison
                        label={t("Temperature")}
                        previous={
                          vitalResult.previous_vitals.temperature
                        }
                        current={
                          vitalResult.new_vitals.temperature
                        }
                        suffix="°C"
                      />

                    </div>

                    <div className="mt-5 rounded-lg bg-white p-4">

                      <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                        {t("New AI Recommendation")}
                      </p>

                      <p className="mt-1 text-2xl font-bold text-slate-900">
                        ESI-{vitalResult.assessment.esi_level}
                      </p>

                      <p className="mt-1 text-sm text-slate-600">
                        {t("Confidence")}{" "}
                        {Math.round(
                          vitalResult.assessment.confidence * 100,
                        )}
                        %
                      </p>

                    </div>

                    {vitalResult.assessment.reasoning.length > 0 && (
                      <div className="mt-4">

                        <p className="text-sm font-semibold text-slate-800">
                          {t("Re-triage reasoning")}
                        </p>

                        <ul className="mt-2 space-y-2">
                          {vitalResult.assessment.reasoning.map(
                            (reason, index) => (
                              <Reason
                                key={index}
                                text={reason}
                              />
                            ),
                          )}
                        </ul>

                      </div>
                    )}

                  </div>
                )}

              </section>

              {/* ================= AI RECOMMENDATION ================= */}

              {/* ================= TRIAGE STATUS ================= */}

<section className="mt-6">

  <div className="grid gap-4 sm:grid-cols-2">

    {/* Current approved ESI */}
    <div className="rounded-xl border border-blue-200 bg-blue-50 p-5">
      <p className="text-sm font-semibold text-blue-700">
        {t("Current Approved ESI")}
      </p>

      <p className="mt-2 text-3xl font-bold text-slate-900">
        {currentEsi !== null
          ? `ESI-${currentEsi}`
          : "—"}
      </p>

      <p className="mt-1 text-xs text-slate-500">
        {t("Current priority in the waiting queue")}
      </p>
    </div>

    {/* AI recommendation */}
    <div className="rounded-xl border border-slate-200 bg-white p-5">

      <div className="flex items-start justify-between gap-4">

        <div>
          <p className="text-sm font-semibold text-slate-500">
            {t("New AI Recommendation")}
          </p>

          <p className="mt-2 text-3xl font-bold text-slate-900">
            ESI-{assessment.esi_level}
          </p>

          <p className="mt-1 text-sm text-slate-600">
            {getEsiDescription(
              assessment.esi_level,
            )}
          </p>
        </div>

        <div className="w-fit rounded-lg bg-white px-4 py-2 shadow-sm">
          <p className="text-xs text-slate-500">
            {t("Confidence")}
          </p>

          <p className="text-lg font-bold text-slate-900">
            {Math.round(
              assessment.confidence * 100,
            )}
            %
          </p>
        </div>

      </div>

    </div>

  </div>

</section>

              {/* ================= REASONING ================= */}

              <AssessmentReasoning assessment={assessment} />

              {/* ================= COORDINATOR DECISION ================= */}

              <section className="mt-6">
                <h3 className="text-sm font-semibold text-slate-900">
                  {t("Coordinator Decision")}
                </h3>

                <p className="mt-1 text-sm text-slate-500">
                  {t("The AI recommendation does not change the patient's priority automatically.")}
                </p>

                {!decision && !overrideMode && (
                  <div className="mt-4 flex flex-col gap-3 sm:flex-row">
                    <button
                      type="button"
                      onClick={handleConfirm}
                      className="flex-1 rounded-lg bg-slate-900 px-4 py-3 text-sm font-semibold text-white transition hover:bg-slate-700"
                    >
                      Confirm AI Recommendation: ESI-{assessment.esi_level}
                    </button>

                    <button
                      type="button"
                      onClick={() =>
                        setOverrideMode(true)
                      }
                      className="flex-1 rounded-lg border border-slate-300 bg-white px-4 py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
                    >
                      {t("Override Recommendation")}
                    </button>
                  </div>
                )}
 
                
                {overrideMode && !decision && (
                  <div className="mt-4 rounded-xl border border-amber-200 bg-amber-50 p-4">
                    <h4 className="font-semibold text-slate-900">
                      {t("Override AI Recommendation")}
                    </h4>

                    <p className="mt-1 text-sm text-slate-600">
                      {t(
          "Select the coordinator's final ESI level and record why the recommendation was overridden.",
        )}
                    </p>

                    <div className="mt-4">
                      <label
                        htmlFor="override-esi"
                        className="text-sm font-medium text-slate-700"
                      >
                         {t("Final ESI Level")}
                      </label>

                      <select
                        id="override-esi"
                        value={overrideEsi}
                        onChange={(event) =>
                          setOverrideEsi(
                            event.target.value,
                          )
                        }
                        className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                      >
                        <option value="1">ESI-1</option>
                        <option value="2">ESI-2</option>
                        <option value="3">ESI-3</option>
                        <option value="4">ESI-4</option>
                        <option value="5">ESI-5</option>
                      </select>
                    </div>

                    <div className="mt-4">
                      <label
                        htmlFor="override-reason"
                        className="text-sm font-medium text-slate-700"
                      >
                         {t("Reason for Override")}
                      </label>

                      <textarea
                        id="override-reason"
                        value={overrideReason}
                        onChange={(event) =>
                          setOverrideReason(
                            event.target.value,
                          )
                        }
                        placeholder={t(
            "Explain the clinical reason for overriding the recommendation...",
          )}
                        rows={4}
                        className="mt-1 w-full resize-none rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                      />
                    </div>

                    <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:justify-end">
                      <button
                        type="button"
                        onClick={() =>
                          setOverrideMode(false)
                        }
                        className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
                      >
                        {t("Cancel")}
                      </button>

                      <button
                        type="button"
                        disabled={!overrideReason.trim()}
                        onClick={handleOverride}
                        className="rounded-lg bg-amber-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-amber-700 disabled:cursor-not-allowed disabled:opacity-40"
                      >
                         {t("Save Override")}
                      </button>
                    </div>
                  </div>
                )}

                {decision === "confirmed" && (
                  <div className="mt-4">
                    <DecisionSuccess
                      title={`ESI-${assessment.esi_level} Confirmed`}
                      description="Coordinator confirmed the AI recommendation."
                    />
                  </div>
                )}

                {decision === "override" && (
                  <div className="mt-4">
                    <DecisionSuccess
                      title={`ESI-${overrideEsi} Selected`}
                      description={t(
          "Coordinator confirmed the AI recommendation.",
        )} />

                    <div className="mt-3 rounded-lg bg-slate-50 p-4">
                      <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                        {t("Override Reason")}
                      </p>

                      <p className="mt-1 text-sm text-slate-600">
                        {overrideReason}
                      </p>
                    </div>
                  </div>
                )}
              </section>
            </>
          )}

          

          <div className="h-4" />
        </div>
      </div>

       
  <div className="mx-4 my-2 rounded-xl border border-emerald-200 bg-emerald-50 p-4">
    <div className="flex items-center justify-between gap-4">
      <div>
         <p className="text-sm font-semibold text-emerald-900">
        {t("Patient ready for care")}
      </p>

      <p className="mt-1 text-xs text-emerald-700">
        {t(
          "Mark this patient as having entered active care.",
        )}
      </p>
      </div>

      <button
        type="button"
        disabled={takingToCare}
        onClick={handleTakeToCare}
        className="
          shrink-0
          rounded-lg
          bg-emerald-600
          px-4
          py-2
          text-sm
          font-semibold
          text-white
          transition
          hover:bg-emerald-700
          disabled:cursor-not-allowed
          disabled:opacity-50
        "
      >
        {takingToCare
        ? t("Updating...")
        : t("Take Patient to Care")}
      </button>
    </div>
  </div>

      {/* ================= FOOTER ================= */}

      <div className="shrink-0 border-t border-slate-200 bg-slate-50 px-6 py-3">
        <p className="text-xs leading-relaxed text-slate-500">
          {t("AI provides decision support. Final clinical responsibility remains with the coordinator.")}
        </p>
      </div>
    </DialogContent>
  </Dialog>
);
    
}

/* ================= INFO ================= */

function Info({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-lg bg-slate-50 p-3">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
        {label}
      </p>

      <p className="mt-1 text-sm font-semibold text-slate-800">
        {value}
      </p>
    </div>
  );
}

/* ================= REASON ================= */

function Reason({
  text,
}: {
  text: string;
}) {
  return (
    <li className="flex items-start gap-3 text-sm leading-relaxed text-slate-600">
      <span className="mt-2 h-2 w-2 shrink-0 rounded-full bg-blue-500" />

      <span>{text}</span>
    </li>
  );
}

/* ================= ESI DESCRIPTION ================= */

function getEsiDescription(esiLevel: number): string {
  switch (esiLevel) {
    case 1:
      return "Immediate life-saving intervention required";
    case 2:
      return "High priority assessment recommended";
    case 3:
      return "Stable but requires emergency department resources";
    case 4:
      return "Lower-acuity patient requiring limited resources";
    case 5:
      return "Lower-acuity patient requiring minimal resources";
    default:
      return "Triage assessment";
  }
}

/* ================= SUCCESS ================= */

function DecisionSuccess({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  const {t} = useLanguage();
  return (
    <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4">
      <div className="flex items-start gap-3">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-emerald-100 font-semibold text-emerald-700">
          ✓
        </div>

        <div>
          <h4 className="font-semibold text-emerald-900">
            {title}
          </h4>

          <p className="mt-1 text-sm text-emerald-700">
            {description}
          </p>

          <p className="mt-2 text-xs text-emerald-600">
            {t("Decision recorded for audit.")}
          </p>
        </div>
      </div>
    </div>
  );
}

function AssessmentReasoning({
  assessment,
}: {
  assessment: {
    assessment_id: number;
    reasoning: string[];
  };
}) {
  const {t} = useLanguage();
  const [explanation, setExplanation] = useState<string | null>(null);
  const [loadingExplanation, setLoadingExplanation] = useState(true);
  const [explanationError, setExplanationError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadExplanation() {
      try {
        setLoadingExplanation(true);
        setExplanationError(null);

        const data = await getAssessmentExplanation(assessment.assessment_id);

        if (!cancelled) {
          setExplanation(data.explanation);
        }
      } catch (err) {
        console.error("Failed to load AI explanation:", err);
        if (!cancelled) {
          setExplanationError(
            err instanceof Error ? err.message : "Unable to load explanation",
          );
        }
      } finally {
        if (!cancelled) {
          setLoadingExplanation(false);
        }
      }
    }

    loadExplanation();

    return () => {
      cancelled = true;
    };
  }, [assessment.assessment_id]);

  return (
    <section className="mt-6">
      <h3 className="text-sm font-semibold text-slate-900">
        {t("Why was this recommended?")}
      </h3>

      {loadingExplanation ? (
        <p className="mt-3 text-sm text-slate-400">
          {t("Generating explanation...")}
        </p>
      ) : explanationError ? (
        assessment.reasoning.length > 0 ? (
          <ul className="mt-3 space-y-3">
            {assessment.reasoning.map((reason, index) => (
              <Reason key={index} text={reason} />
            ))}
          </ul>
        ) : (
          <p className="mt-3 text-sm text-slate-500">
            {t("No reasoning details were provided.")}
          </p>
        )
      ) : explanation ? (
        <p className="mt-3 whitespace-pre-line text-sm text-slate-700">
          {explanation}
        </p>
      ) : (
        <p className="mt-3 text-sm text-slate-500">
          {t("No reasoning details were provided.")}
        </p>
      )}
    </section>
  );
}

function VitalInput({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <div>
      <label className="text-xs font-medium text-slate-600">
        {label}
      </label>

      <input
        type="number"
        value={value}
        onChange={(event) =>
          onChange(event.target.value)
        }
        className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
      />
    </div>
  );
}

function VitalComparison({
  label,
  previous,
  current,
  suffix,
}: {
  label: string;
  previous: number | null;
  current: number | null;
  suffix: string;
}) {
  if (current === null || current === undefined) {
    return null;
  }

  const changed =
    previous !== null &&
    previous !== undefined &&
    previous !== current;

    const {t} = useLanguage();
  return (
    <div className="rounded-lg bg-white p-3">
      <p className="text-xs font-medium text-slate-400">
        {label}
      </p>

      <p className="mt-1 text-sm font-semibold text-slate-800">
        {previous ?? "—"}
        {suffix}
        {" → "}
        {current}
        {suffix}
      </p>

      {changed && (
        <p className="mt-1 text-xs font-medium text-blue-600">
          {t("Changed")}
        </p>
      )}
    </div>
  );
}

export default PatientReview;