import { useEffect, useState, useRef } from "react";

import {
  getWaitingQueue,
  triggerRetriage,
  submitManualEsi,
  takePatientToCare,
  type WaitingQueuePatient,
} from "../services/api";

import { Button } from "./ui/button";
import { Card } from "./ui/card";
import { useLanguage } from "../context/LanguageContext";
import AiDisclosure from "./AiDisclosure";
type PatientQueueProps = {
  refreshKey: number;
  onRetriageTriggered: () => void;
  onPatientsLoaded: (patients: WaitingQueuePatient[]) => void;
};

function PatientQueue({
  refreshKey,
  onRetriageTriggered,
  onPatientsLoaded
}: PatientQueueProps) {

  const [patients, setPatients] = useState<
    WaitingQueuePatient[]
  >([]);

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState<string | null>(null);

  const [selectedPatient, setSelectedPatient] =
    useState<WaitingQueuePatient | null>(null);

  const hasLoadedOnce = useRef(false);

  const { t } = useLanguage();

  useEffect(() => {

    async function loadQueue() {

      try {

        if (!hasLoadedOnce.current) {
          setLoading(true);
        }

        const data = await getWaitingQueue();
        onPatientsLoaded(data.patients);
        setPatients((prev) => {

          const same =
            JSON.stringify(prev) ===
            JSON.stringify(data.patients);

          return same
            ? prev
            : data.patients;
        });

        setError(null);

      } catch (err) {

        console.error(
          "Failed to load waiting queue:",
          err,
        );

        setError(
          err instanceof Error
            ? err.message
            : "Unable to load waiting queue",
        );

      } finally {

        if (!hasLoadedOnce.current) {
          setLoading(false);
          hasLoadedOnce.current = true;
        }

      }
    }

    loadQueue();

  }, [refreshKey]);

  return (
    <section className="mt-4">

      <div className="mb-4">

        <h3 className="text-lg font-semibold text-slate-900">
  {t("Waiting Queue")}
</h3>

<p className="text-sm text-slate-500">
  {t("Current patients awaiting treatment")}
</p>

</div>

<Card className="overflow-hidden p-0">

  {/* Table header */}
  <div className="hidden grid-cols-12 border-b border-slate-100 bg-slate-50 px-5 py-3 text-xs font-semibold uppercase tracking-wide text-slate-500 sm:grid">

    <div className="col-span-2">
      {t("Patient")}
    </div>

    <div className="col-span-4">
      {t("Complaint")}
    </div>

    <div className="col-span-2">
      {t("Priority")}
    </div>

    <div className="col-span-2">
      {t("Wait Time")}
    </div>

    <div className="col-span-2 text-right">
      {t("Status")}
    </div>

  </div>

  {/* Loading */}
  {loading && (
    <div className="p-6 text-sm text-slate-500">
      {t("Loading waiting queue...")}
    </div>
  )}

  {/* Error */}
  {!loading && error && (
    <div className="p-6">

      <p className="text-sm font-medium text-red-600">
        {t("Unable to load waiting queue")}
      </p>

      <p className="mt-1 text-xs text-slate-500">
        {error}
      </p>

    </div>
  )}

  {/* Empty */}
  {!loading &&
    !error &&
    patients.length === 0 && (

      <div className="p-12 text-center">

        <p className="text-sm font-semibold text-slate-800">
          {t("No patients currently waiting")}
        </p>

        <p className="mt-1 text-xs text-slate-500">
          {t("Patients will appear here after coordinator review.")}
        </p>

      </div>

    )}
        {/* Patients */}
        {!loading &&
          !error &&
          patients.map((patient) => (

            <PatientRow
              key={patient.patient_id}
              patient={patient}
              onUpdate={() =>
                setSelectedPatient(patient)
              }
            />

          ))}

      </Card>

      {/* Patient Event Panel */}
      {selectedPatient && (

        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 px-4">

          <PatientEventPanel
            patient={selectedPatient}

            onClose={() =>
              setSelectedPatient(null)
            }

            onComplete={() => {
              setSelectedPatient(null);
              onRetriageTriggered();
            }}
          />

        </div>

      )}

    </section>
  );
}


function PatientRow({
  patient,
  onUpdate,
}: {
  patient: WaitingQueuePatient;
  onUpdate: () => void;
}) {

  const priority =
    getPriority(patient.esi_level);
const {t} = useLanguage();
  return (
    <div className="grid grid-cols-1 gap-3 border-b border-slate-100 px-5 py-4 last:border-b-0 sm:grid-cols-12 sm:items-center sm:gap-0">

      {/* Patient */}
      <div className="sm:col-span-2">

        <span className="font-semibold text-slate-900">
          {patient.patient_uuid}
        </span>

      </div>

      {/* Complaint */}
      <div className="sm:col-span-4">

        <span className="text-sm text-slate-700">
          {patient.chief_complaint}
        </span>

      </div>

      {/* Priority */}
      <div className="sm:col-span-2">

        <span
          className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ${priority.badge}`}
        >
          ESI-{patient.esi_level}
        </span>

      </div>

      {/* Wait Time */}
      <div className="text-sm text-slate-600 sm:col-span-2">

        {Math.round(
          patient.wait_time_minutes,
        )}{" "}
        min

      </div>

      {/* Status */}
      <div className="flex items-center justify-between gap-3 sm:col-span-2 sm:justify-end">

       <span className="text-xs font-medium text-slate-500">
  {t("Waiting")}
</span>

<Button onClick={onUpdate}>
  {t("Update")}
</Button>
      </div>

    </div>
  );
}


function getPriority(
  esi: WaitingQueuePatient["esi_level"],
) {

  switch (esi) {

    case 1:
      return {
        badge: "bg-red-100 text-red-700",
      };

    case 2:
      return {
        badge: "bg-orange-100 text-orange-700",
      };

    case 3:
      return {
        badge: "bg-amber-100 text-amber-700",
      };

    case 4:
      return {
        badge: "bg-blue-100 text-blue-700",
      };

    case 5:
      return {
        badge: "bg-slate-100 text-slate-600",
      };

    default:
      return {
        badge: "bg-slate-100 text-slate-600",
      };
  }
}


type AssessmentResult = {
  assessment_id?: number | null;
  esi_level: number;
  confidence: number | null;
  confidence_band: string | null;
  reasoning: string[];
  auto_escalate_for_review: boolean;
};

type PanelMode = "manual" | "vitals" | "observation";

function PatientEventPanel({
  patient,
  onClose,
  onComplete,
}: {
  patient: WaitingQueuePatient;
  onClose: () => void;
  onComplete: () => void;
}) {
  const [mode, setMode] = useState<PanelMode>("manual");
  const [phase, setPhase] = useState<"form" | "result">("form");
  const [aiResult, setAiResult] = useState<AssessmentResult | null>(null);
  const [coordinatorEsi, setCoordinatorEsi] = useState<number | null>(null);
  // Manual override
  const [manualEsi, setManualEsi] = useState("");
  const [manualNote, setManualNote] = useState("");

  // Vitals
  const [spo2, setSpo2] = useState("");
  const [heartRate, setHeartRate] = useState("");
  const [systolic, setSystolic] = useState("");
  const [diastolic, setDiastolic] = useState("");
  const [temperature, setTemperature] = useState("");
const [respRate, setRespRate] = useState("");
const [pain, setPain] = useState("");
  // Observation
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [takingToCare, setTakingToCare] = useState(false);

  const switchMode = (next: PanelMode) => {
    setMode(next);
    setPhase("form");
    setAiResult(null);
    setError(null);
  };

  const handleManualSubmit = async () => {
    if (!manualEsi) {
      setError("Select an ESI level.");
      return;
    }
    try {
      setLoading(true);
      setError(null);

      await submitManualEsi({
        patient_id: patient.patient_id,
        esi_level: Number(manualEsi),
        note: manualNote,
      });

      // No AI result to show for a manual change -
      // it goes straight to Needs Attention for confirmation.
      onComplete();
    } catch (err) {
      console.error("Failed to submit manual ESI:", err);
      setError(
        err instanceof Error ? err.message : "Unable to update ESI level",
      );
    } finally {
      setLoading(false);
    }
  };

  const handleEventSubmit = async (
    eventType: "vital_change" | "observation",
  ) => {
    try {
      setLoading(true);
      setError(null);

      const result = await triggerRetriage({
        patient_id: patient.patient_id,
        event_type: eventType,
        data: {
          description,
          new_vitals:
            eventType === "vital_change"
              ? {
                  spo2: spo2 ? Number(spo2) : null,
                  heart_rate: heartRate ? Number(heartRate) : null,
                  bp_systolic: systolic ? Number(systolic) : null,
                  bp_diastolic: diastolic ? Number(diastolic) : null,
                  temperature: temperature ? Number(temperature) : null,
                  respiratory_rate: respRate ? Number(respRate) : null,
                  pain: pain ? Number(pain) : null,
                }
              : {},
        },
      });

      setAiResult(result);
      setPhase("result");
    } catch (err) {
      console.error("Failed to trigger re-triage:", err);
      setError(
        err instanceof Error ? err.message : "Unable to trigger re-triage",
      );
    } finally {
      setLoading(false);
    }
  };

  const handleTakeToCare = async () => {
  try {
    setTakingToCare(true);
    setError(null);

    await takePatientToCare(patient.patient_id);

    onComplete();
  } catch (err) {
    console.error("Failed to take patient to care:", err);

    setError(
      err instanceof Error
        ? err.message
        : "Unable to move patient to care",
    );
  } finally {
    setTakingToCare(false);
  }
};
 const {t} = useLanguage();
  const triageComparison =
  coordinatorEsi === null || aiResult === null
    ? null
    : coordinatorEsi < aiResult.esi_level
      ? "under-triage"
      : coordinatorEsi > aiResult.esi_level
        ? "over-triage"
        : "aligned";

  return (
  <div className="w-full max-w-lg rounded-2xl border border-slate-200 bg-white p-6 shadow-xl">

    {/* Header */}
    <div className="flex items-start justify-between">
      <div>
        <h4 className="font-semibold text-slate-900">
          {t("Update Patient")}
        </h4>

        <p className="mt-1 text-xs text-slate-500">
          {patient.patient_uuid} · {patient.chief_complaint}
        </p>
      </div>

      <button
        type="button"
        onClick={onClose}
        className="text-sm text-slate-500 hover:text-slate-900"
      >
        {t("Close")}
      </button>
    </div>

    <AiDisclosure compact />

    {/* Mode switcher */}
    {phase === "form" && (
      <div className="mt-4 grid grid-cols-3 gap-2">

        <button
          type="button"
          onClick={() => switchMode("manual")}
          className={`rounded-lg border px-3 py-2 text-xs font-semibold ${
            mode === "manual"
              ? "border-blue-500 bg-blue-50 text-blue-700"
              : "border-slate-200 text-slate-600"
          }`}
        >
          {t("Change ESI")}
        </button>

        <button
          type="button"
          onClick={() => switchMode("vitals")}
          className={`rounded-lg border px-3 py-2 text-xs font-semibold ${
            mode === "vitals"
              ? "border-blue-500 bg-blue-50 text-blue-700"
              : "border-slate-200 text-slate-600"
          }`}
        >
          {t("Update Vitals")}
        </button>

        <button
          type="button"
          onClick={() => switchMode("observation")}
          className={`rounded-lg border px-3 py-2 text-xs font-semibold ${
            mode === "observation"
              ? "border-orange-500 bg-orange-50 text-orange-700"
              : "border-slate-200 text-slate-600"
          }`}
        >
          {t("Condition Worsened")}
        </button>

      </div>
    )}

    {/* ===== FORM: Manual ESI ===== */}
    {phase === "form" && mode === "manual" && (
      <div className="mt-5">

        <label className="text-xs font-medium text-slate-600">
          {t("New ESI Level")}
        </label>

        <select
          value={manualEsi}
          onChange={(e) => setManualEsi(e.target.value)}
          className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
        >
          <option value="">
            {t("Select ESI level")}
          </option>

          <option value="1">
            {t("ESI-1 · Resuscitation")}
          </option>

          <option value="2">
            {t("ESI-2 · Emergent")}
          </option>

          <option value="3">
            {t("ESI-3 · Urgent")}
          </option>

          <option value="4">
            {t("ESI-4 · Less urgent")}
          </option>

          <option value="5">
            {t("ESI-5 · Non-urgent")}
          </option>
        </select>

        <label className="mt-3 block text-xs font-medium text-slate-600">
          {t("Reason (optional)")}
        </label>

        <textarea
          value={manualNote}
          onChange={(e) => setManualNote(e.target.value)}
          rows={2}
          placeholder={t("Why is the ESI level changing?")}
          className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
        />

      </div>
    )}

    {/* ===== FORM: Vitals ===== */}
{phase === "form" && mode === "vitals" && (
  <div className="mt-5">

    <p className="text-sm font-medium text-slate-700">
      {t("Updated Vitals")}
    </p>

    <p className="mt-1 text-xs text-slate-500">
      {t("Enter the patient's latest vital signs.")}
    </p>

    <div className="mt-3 grid grid-cols-2 gap-3">

      {/* SpO2 */}
      <div>
        <label className="text-xs font-medium text-slate-600">
          {t("SpO₂ (%)")}
        </label>

        <input
          type="number"
          value={spo2}
          onChange={(e) => setSpo2(e.target.value)}
          placeholder="97"
          className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
        />
      </div>

      {/* Heart Rate */}
      <div>
        <label className="text-xs font-medium text-slate-600">
          {t("Heart Rate")}
        </label>

        <input
          type="number"
          value={heartRate}
          onChange={(e) => setHeartRate(e.target.value)}
          placeholder="80"
          className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
        />
      </div>

      {/* Respiratory Rate */}
      <div>
        <label className="text-xs font-medium text-slate-600">
          {t("Respiratory Rate")}
        </label>

        <input
          type="number"
          value={respRate}
          onChange={(e) => setRespRate(e.target.value)}
          placeholder="18"
          className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
        />
      </div>

      {/* Systolic BP */}
      <div>
        <label className="text-xs font-medium text-slate-600">
          {t("Systolic BP")}
        </label>

        <input
          type="number"
          value={systolic}
          onChange={(e) => setSystolic(e.target.value)}
          placeholder="120"
          className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
        />
      </div>

      {/* Diastolic BP */}
      <div>
        <label className="text-xs font-medium text-slate-600">
          {t("Diastolic BP")}
        </label>

        <input
          type="number"
          value={diastolic}
          onChange={(e) => setDiastolic(e.target.value)}
          placeholder="80"
          className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
        />
      </div>

      {/* Temperature */}
      <div>
        <label className="text-xs font-medium text-slate-600">
          {t("Temperature (°C)")}
        </label>

        <input
          type="number"
          step="0.1"
          value={temperature}
          onChange={(e) => setTemperature(e.target.value)}
          placeholder="36.8"
          className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
        />
      </div>

      {/* Pain */}
      <div>
        <label className="text-xs font-medium text-slate-600">
          {t("Pain Level")}
        </label>

        <input
          type="number"
          min="0"
          max="10"
          value={pain}
          onChange={(e) => setPain(e.target.value)}
          placeholder="0"
          className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
        />
      </div>

    </div>
  </div>
)}

    {/* ===== FORM: Condition Worsened ===== */}
    {phase === "form" && mode === "observation" && (
      <div className="mt-5 rounded-lg border border-orange-200 bg-orange-50 p-3">

        <p className="text-sm font-semibold text-orange-800">
          {t("Condition worsened")}
        </p>

        <p className="mt-1 text-xs text-orange-700">
          {t(
            "This runs an urgent re-assessment and flags the patient for immediate review.",
          )}
        </p>

        <label className="mt-3 block text-xs font-medium text-slate-600">
          {t("Describe what changed")}
        </label>

        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={3}
          placeholder={t(
            "Describe the deterioration in the patient's condition...",
          )}
          className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-orange-500 focus:ring-2 focus:ring-orange-100"
        />

      </div>
    )}

    {/* ===== RESULT: AI recommendation ===== */}
    {phase === "result" && aiResult && (
      <div className="mt-5">

        <div
          className={`rounded-lg border p-4 ${
            aiResult.esi_level <= 2
              ? "border-red-200 bg-red-50"
              : "border-slate-200 bg-slate-50"
          }`}
        >

          <div className="flex items-center justify-between">

            <span className="text-sm font-semibold text-slate-900">
              {t("AI Recommendation")}: ESI-{aiResult.esi_level}
            </span>

            <div>
  <p className="text-xs font-medium text-slate-400">
    {t("Confidence")}
  </p>

  <p className="mt-1 text-sm font-semibold text-slate-900">
    {aiResult.confidence_band === "emergency_override"
      ? t("N/A")
      : aiResult.confidence !== null
        ? `${Math.round(aiResult.confidence * 100)}%`
        : t("N/A")}
  </p>
</div>

<div>
  <p className="text-xs font-medium text-slate-400">
    {t("Confidence Band")}
  </p>

  <p className="mt-1 text-sm font-semibold text-slate-900">
    {aiResult.confidence_band === "emergency_override"
      ? t("Emergency Override")
      : aiResult.confidence_band
        ? t(aiResult.confidence_band)
        : t("N/A")}
  </p>
</div>

<div>
  <p className="text-xs font-medium text-slate-400">
    {t("Confidence Band")}
  </p>

  <p className="mt-1 text-sm font-semibold text-slate-900">
    {aiResult.confidence_band === "emergency_override"
      ? t("Emergency Override")
      : aiResult.confidence_band
        ? t(aiResult.confidence_band)
        : t("N/A")}
  </p>
</div>
          </div>

          {aiResult.reasoning.length > 0 && (
            <ul className="mt-2 list-disc space-y-1 pl-4 text-xs text-slate-600">
              {aiResult.reasoning.map((r, i) => (
                <li key={i}>{r}</li>
              ))}
            </ul>
          )}

        </div>

        {/* Coordinator Assessment */}
        <div className="mt-4 rounded-lg border border-slate-200 bg-slate-50 p-4">

          <p className="text-sm font-semibold text-slate-800">
            {t("Coordinator Assessment")}
          </p>

          <p className="mt-1 text-xs text-slate-500">
            {t(
              "Select the ESI level you believe is appropriate for this patient.",
            )}
          </p>

          <div className="mt-3 grid grid-cols-5 gap-2">
            {[1, 2, 3, 4, 5].map((esi) => (
              <button
                key={esi}
                type="button"
                onClick={() => setCoordinatorEsi(esi)}
                className={`rounded-lg border px-3 py-2 text-sm font-semibold transition ${
                  coordinatorEsi === esi
                    ? "border-blue-500 bg-blue-50 text-blue-700"
                    : "border-slate-200 bg-white text-slate-600 hover:border-slate-300"
                }`}
              >
                ESI-{esi}
              </button>
            ))}
          </div>

        </div>

        {triageComparison && (
          <div
            className={`mt-3 rounded-lg border p-3 ${
              triageComparison === "under-triage"
                ? "border-red-200 bg-red-50"
                : triageComparison === "over-triage"
                  ? "border-amber-200 bg-amber-50"
                  : "border-emerald-200 bg-emerald-50"
            }`}
          >

            <p
              className={`text-sm font-semibold ${
                triageComparison === "under-triage"
                  ? "text-red-700"
                  : triageComparison === "over-triage"
                    ? "text-amber-700"
                    : "text-emerald-700"
              }`}
            >
              {triageComparison === "under-triage"
                ? t("Under-triage detected")
                : triageComparison === "over-triage"
                  ? t("Over-triage detected")
                  : t("Triage aligned")}
            </p>

            <p className="mt-1 text-xs text-slate-600">
              {t("AI recommendation")}: ESI-{aiResult.esi_level}
              {" · "}
              {t("Coordinator assessment")}: ESI-{coordinatorEsi}
            </p>

          </div>
        )}

        {(mode === "observation" ||
          aiResult.auto_escalate_for_review) && (
          <div className="mt-3 rounded-lg border border-red-200 bg-red-50 p-3">

            <p className="text-sm font-semibold text-red-700">
              {mode === "observation"
                ? t("Recommended: take patient to care immediately")
                : t(
                    "This case is flagged for urgent coordinator review",
                  )}
            </p>

            {mode === "observation" && (
              <button
                type="button"
                disabled={takingToCare}
                onClick={handleTakeToCare}
                className="mt-3 w-full rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-red-700 disabled:opacity-50"
              >
                {takingToCare
                  ? t("Moving to care...")
                  : t("Take Patient to Care")}
              </button>
            )}

          </div>
        )}

        <p className="mt-3 text-xs text-slate-500">
          {t(
            "This assessment now appears in Needs Attention awaiting coordinator confirmation.",
          )}
        </p>

      </div>
    )}

    {/* Error */}
    {error && (
      <p className="mt-3 text-sm text-red-600">
        {error}
      </p>
    )}

    {/* Actions */}
    {phase === "form" ? (
      <button
        type="button"
        disabled={loading}
        onClick={() => {
          if (mode === "manual") {
            handleManualSubmit();
          } else {
            handleEventSubmit(
              mode === "vitals"
                ? "vital_change"
                : "observation",
            );
          }
        }}
        className="mt-4 w-full rounded-lg bg-slate-900 px-4 py-3 text-sm font-semibold text-white transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {loading
          ? t("Submitting...")
          : mode === "manual"
            ? t("Done")
            : t("Trigger Re-triage")}
      </button>
    ) : (
      <button
        type="button"
        onClick={onComplete}
        className="mt-4 w-full rounded-lg bg-slate-900 px-4 py-3 text-sm font-semibold text-white transition hover:bg-slate-700"
      >
        {t("Done")}
      </button>
    )}

  </div>
);
}

export default PatientQueue;