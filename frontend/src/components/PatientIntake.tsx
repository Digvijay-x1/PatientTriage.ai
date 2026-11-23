import { useState, useEffect } from "react";
import { registerPatient, runTriage } from "../services/api";
import { useLanguage } from "../context/LanguageContext";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "./ui/dialog";
import AiDisclosure from "./AiDisclosure";

type PatientIntakeProps = {
  open: boolean;
  onClose: () => void;
  onPatientAdded: () => void;
};

function PatientIntake({
  open,
  onPatientAdded,
  onClose,
}: PatientIntakeProps) {
  const [patientId, setPatientId] = useState("");
  const [age, setAge] = useState("");
  const [chiefComplaint, setChiefComplaint] = useState("");
  const [sex, setSex] =  useState("female");
  const [spo2, setSpo2] = useState("");
  const [systolic, setSystolic] = useState("");
  const [diastolic, setDiastolic] = useState("");
  const [heartRate, setHeartRate] = useState("");
  const [temperature, setTemperature] = useState("");
  
const [historyCardiac, setHistoryCardiac] = useState(false);
const [historyRespiratory, setHistoryRespiratory] = useState(false);
const [historyDiabetes, setHistoryDiabetes] = useState(false);
const [historyRenal, setHistoryRenal] = useState(false);
const [historyHypertension, setHistoryHypertension] = useState(false);
const hasPriorRecord = historyCardiac || historyRespiratory || historyDiabetes || historyRenal || historyHypertension;
  const [responsiveness, setResponsiveness] =
    useState("alert");

  const [breathing, setBreathing] =
    useState("normal");

  const [distressLevel, setDistressLevel] =
    useState("moderate");

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [result, setResult] = useState<{
    patientId: number;
    assessmentId: number;
    esiLevel: number;
    confidence: number;
    confidenceBand: string;
    reasoning: string[];
    autoEscalate: boolean;
  } | null>(null);

  const [respRate, setrespRate] = useState("");
  const { t } = useLanguage();

  const [pain, setPain] = useState<string>("");

  useEffect(() => {
  if (open) {
    setResult(null);
    setError(null);
  }
}, [open]);
  async function handleSubmit(
    event: React.FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    setSubmitting(true);
    setError(null);

   try {
  // 1. Register patient
  const patient = await registerPatient({
    patient_id: patientId,
    age: Number(age),
    chief_complaint: chiefComplaint,
    sex: sex,

    vitals: {
      spo2: Number(spo2),
      bp_systolic: Number(systolic),
      bp_diastolic: Number(diastolic),
      heart_rate: Number(heartRate),
      temperature: Number(temperature),
      pain: pain === "" ? undefined : Number(pain),
      respiratory_rate: Number(respRate),
    },

    observed: {
      responsiveness,
      breathing,
      distress_level: distressLevel,
    },

    // Medical history
    has_prior_record: hasPriorRecord,
    history_cardiac: historyCardiac,
    history_respiratory: historyRespiratory,
    history_diabetes: historyDiabetes,
    history_renal: historyRenal,
    history_hypertension: historyHypertension,
  });

      // 2. Run AI triage
      const triage = await runTriage(
        patient.patient_id,
      );

      setResult({
        patientId: patient.patient_id,
        assessmentId: triage.assessment_id,
        esiLevel: triage.esi_level,
        confidence: triage.confidence,
        confidenceBand: triage.confidence_band,
        reasoning: triage.reasoning,
        autoEscalate:
          triage.auto_escalate_for_review,
      });
      onPatientAdded();
    } catch (err) {
      console.error(err);

      setError(
        err instanceof Error
          ? err.message
          : "Unable to register patient.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  function handleClose() {
    if (submitting) return;
    
    setResult(null);
    setError(null);
    onClose();
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(value) => {
        if (!value) {
          handleClose();
        }
      }}
    >
      <DialogContent
        showCloseButton
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
        {/* Header */}
        <DialogHeader
          className="
            shrink-0
            border-b
            border-slate-200
            px-6
            py-5
            text-left
          "
        >
         <DialogTitle className="text-xl font-bold text-slate-900">
  {t("Add Patient")}
</DialogTitle>

<p className="mt-1 text-sm text-slate-500">
  {t("Capture the information available during the patient's initial arrival.")}
</p>

<AiDisclosure compact />
        </DialogHeader>

        {/* Scrollable body */}
        <div className="min-h-0 flex-1 overflow-y-auto">
          <div className="px-6 py-6">

            {/* ================= FORM ================= */}

            {!result && (
              <form
                onSubmit={handleSubmit}
                className="space-y-6"
              >
                {/* Patient Information */}
                <section>
                  <h2 className="text-sm font-semibold text-slate-900">
  {t("Patient Information")}
</h2>

                  <div className="mt-4 grid gap-4 sm:grid-cols-2">

                    <Field
  label={t("Patient ID")}
  value={patientId}
  onChange={setPatientId}
  placeholder="P001"
  required
/>

<Field
  label={t("Age")}
  type="number"
  value={age}
  onChange={setAge}
  placeholder="52"
  required
/>
<SelectField
  label={t("Sex")}
  value={sex}
  onChange={setSex}
  options={[
    "female",
    "male",
  ]}
/>

                    <div className="sm:col-span-2">
                      <label className="text-sm font-medium text-slate-700">
                        {t("Chief Complaint")}
                      </label>

                      <textarea
                        value={chiefComplaint}
                        onChange={(e) =>
                          setChiefComplaint(
                            e.target.value,
                          )
                        }
                        placeholder="e.g. Chest pain"
                        rows={3}
                        className="
                          mt-1
                          w-full
                          resize-none
                          rounded-lg
                          border
                          border-slate-300
                          px-3
                          py-2
                          text-sm
                          outline-none
                          focus:border-blue-500
                          focus:ring-2
                          focus:ring-blue-100
                        "
                      />
                    </div>
                  </div>
                </section>

                {/* Vitals */}
                <section>
                  <h2 className="text-sm font-semibold text-slate-900">
                    {t("Initial Vitals")}
                  </h2>

                  <p className="mt-1 text-xs text-slate-500">
                     {t("Values available during initial assessment.")}
                  </p>

                  <div className="mt-4 grid gap-4 sm:grid-cols-2">

                    <Field 
  label={t("SpO₂ (%)")} 
  type="number" 
  value={spo2} 
  onChange={setSpo2} 
  placeholder="97" 
/>

<Field 
  label={t("Heart Rate")} 
  type="number" 
  value={heartRate} 
  onChange={setHeartRate} 
  placeholder="102" 
/>

<Field 
  label={t("Systolic BP")} 
  type="number" 
  value={systolic} 
  onChange={setSystolic} 
  placeholder="168" 
/>

<Field 
  label={t("Diastolic BP")} 
  type="number" 
  value={diastolic} 
  onChange={setDiastolic} 
  placeholder="98" 
/>

<Field 
  label={t("Temperature (°C)")} 
  type="number" 
  value={temperature} 
  onChange={setTemperature} 
  placeholder="36.8" 
/>
                  </div>
                </section>

                {/* Observation */}
                <section>
        

 <div>
  <label className="text-xs font-medium text-slate-600">
    {t("Pain Level (0–10)")}
  </label>
  <input
    type="number"
    min={0}
    max={10}
    value={pain}
    onChange={(e) => setPain(e.target.value)}
    placeholder="0"
    className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
  />
</div>

<Field 
  label={t("Respiratory Rate")} 
  type="number" 
  value={respRate} 
  onChange={setrespRate} 
  placeholder="24" 
/>
<div className="mt-4 grid gap-4 sm:grid-cols-3">
 
  

          
  <SelectField 
    label={t("Responsiveness")} 
    value={responsiveness} 
    onChange={setResponsiveness} 
    options={[
      "alert", 
      "confused", 
      "unresponsive",
    ]} 
  />

  <SelectField 
    label={t("Breathing")} 
    value={breathing} 
    onChange={setBreathing} 
    options={[
      "normal", 
      "labored", 
      "fast",
    ]} 
  />

  <SelectField 
    label={t("Distress Level")} 
    value={distressLevel} 
    onChange={setDistressLevel} 
    options={[
      "none", 
      "mild", 
      "moderate", 
      "severe",
    ]} 
  />

  

</div>
<div className="mt-5">
  <p className="text-sm font-medium text-slate-700">
    {t("Medical History")}
  </p>

  <div className="mt-3 grid grid-cols-2 gap-3">

    <label className="flex items-center gap-2 cursor-pointer">
      <input
        type="checkbox"
        checked={historyCardiac}
        onChange={(e) =>
          setHistoryCardiac(e.target.checked)
        }
        className="h-4 w-4 rounded border-slate-300"
      />
      <span className="text-sm text-slate-700">
        {t("Cardiac")}
      </span>
    </label>

    <label className="flex items-center gap-2 cursor-pointer">
      <input
        type="checkbox"
        checked={historyRespiratory}
        onChange={(e) =>
          setHistoryRespiratory(e.target.checked)
        }
        className="h-4 w-4 rounded border-slate-300"
      />
      <span className="text-sm text-slate-700">
        {t("Respiratory")}
      </span>
    </label>

    <label className="flex items-center gap-2 cursor-pointer">
      <input
        type="checkbox"
        checked={historyDiabetes}
        onChange={(e) =>
          setHistoryDiabetes(e.target.checked)
        }
        className="h-4 w-4 rounded border-slate-300"
      />
      <span className="text-sm text-slate-700">
        {t("Diabetes")}
      </span>
    </label>

    <label className="flex items-center gap-2 cursor-pointer">
      <input
        type="checkbox"
        checked={historyRenal}
        onChange={(e) =>
          setHistoryRenal(e.target.checked)
        }
        className="h-4 w-4 rounded border-slate-300"
      />
      <span className="text-sm text-slate-700">
        {t("Renal")}
      </span>
    </label>

    <label className="flex items-center gap-2 cursor-pointer">
      <input
        type="checkbox"
        checked={historyHypertension}
        onChange={(e) =>
          setHistoryHypertension(e.target.checked)
        }
        className="h-4 w-4 rounded border-slate-300"
      />
      <span className="text-sm text-slate-700">
        {t("Hypertension")}
      </span>
    </label>

  </div>
</div>
                </section>

                {/* Error */}
                {error && (
                  <div className="rounded-lg border border-red-200 bg-red-50 p-4">
                    <p className="text-sm font-semibold text-red-700">
                      Unable to process patient
                    </p>

                    <p className="mt-1 text-sm text-red-600">
                      {error}
                    </p>
                  </div>
                )}

                {/* Submit */}
                <button
  type="submit"
  disabled={submitting}
  className="
    w-full
    rounded-lg
    bg-slate-900
    px-5
    py-3
    text-sm
    font-semibold
    text-white
    transition
    hover:bg-slate-700
    disabled:cursor-not-allowed
    disabled:opacity-50
  "
>
  {submitting
    ? t("Registering and assessing...")
    : t("Register Patient & Run Triage")}
</button>
              </form>
            )}

            {/* ================= TRIAGE RESULT ================= */}

            {result && (
              <TriageResult
                result={result}
                onDone={onClose}
              />
            )}

          </div>
        </div>

        {/* Footer */}
        <div className="shrink-0 border-t border-slate-200 bg-slate-50 px-6 py-3">
  <p className="text-xs leading-relaxed text-slate-500">
    {t(
      "AI provides decision support. Final clinical responsibility remains with the coordinator.",
    )}
  </p>
</div>
      </DialogContent>
    </Dialog>
  );
}

/* ================= FIELD ================= */

function Field({
  label,
  value,
  onChange,
  placeholder,
  type = "text",
  required = false,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  type?: string;
  required?: boolean;
}) {
  return (
    <div>
      <label className="text-sm font-medium text-slate-700">
        {label}
      </label>

      <input
        type={type}
        value={value}
        onChange={(e) =>
          onChange(e.target.value)
        }
        placeholder={placeholder}
        required={required}
        className="
          mt-1
          w-full
          rounded-lg
          border
          border-slate-300
          px-3
          py-2
          text-sm
          outline-none
          focus:border-blue-500
          focus:ring-2
          focus:ring-blue-100
        "
      />
    </div>
  );
}

/* ================= SELECT ================= */

function SelectField({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: string[];
}) {
  const { t } = useLanguage();

  return (
    <div>
      <label className="text-sm font-medium text-slate-700">
        {label}
      </label>

      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="
          mt-1
          w-full
          rounded-lg
          border
          border-slate-300
          bg-white
          px-3
          py-2
          text-sm
          outline-none
          focus:border-blue-500
          focus:ring-2
          focus:ring-blue-100
        "
      >
        {options.map((option) => (
          <option
            key={option}
            value={option}
          >
            {t(option)}
          </option>
        ))}
      </select>
    </div>
  );
}
/* ================= TRIAGE RESULT ================= */

function TriageResult({
  result,
  onDone,
}: {
  
  result: {
    patientId: number;
    assessmentId: number;
    esiLevel: number;
    confidence: number;
    confidenceBand: string;
    reasoning: string[];
    autoEscalate: boolean;
  };
  onDone: () => void;
}) {

  const { t } = useLanguage();
  return (
    <div>
      <div className="mb-5">
        <p className="text-sm font-medium text-blue-600">
          {t("Triage Assessment Complete")}
        </p>

        <h2 className="mt-1 text-xl font-bold text-slate-900">
          {t("Patient Assessment")}
        </h2>
      </div>

      <div className="grid gap-3 sm:grid-cols-3">

        <ResultCard 
  label={t("AI ESI")} 
  value={`ESI-${result.esiLevel}`} 
/>

<ResultCard
  label="Confidence"
  value={
    result.confidenceBand === "emergency_override"
      ? "N/A"
      : `${Math.round(result.confidence * 100)}%`
  }
/>

<ResultCard
  label="Confidence Band"
  value={
    result.confidenceBand === "emergency_override"
      ? "Emergency Override"
      : result.confidenceBand
  }
/>
</div>

<div className="mt-6">
  <h3 className="text-sm font-semibold text-slate-900">
    {t("Reasoning")}
  </h3>

  {result.reasoning.length > 0 ? (
    <ul className="mt-3 space-y-2">
      {result.reasoning.map(
        (reason, index) => (
          <li
            key={index}
            className="flex gap-3 text-sm text-slate-600"
          >
            <span className="mt-2 h-2 w-2 shrink-0 rounded-full bg-blue-500" />

            {reason}
          </li>
        ),
      )}
    </ul>
  ) : (
    <p className="mt-2 text-sm text-slate-500">
      {t("No reasoning details were provided.")}
    </p>
  )}
</div>

{result.autoEscalate && (
  <div className="mt-6 rounded-lg border border-amber-200 bg-amber-50 p-4">
    <p className="text-sm font-semibold text-amber-800">
      {t("Coordinator Review Required")}
    </p>

    <p className="mt-1 text-sm text-amber-700">
      {t(
        "The assessment has been automatically escalated for coordinator review.",
      )}
    </p>
  </div>
)}

      <button
        type="button"
        onClick={onDone}
        className="
          mt-6
          w-full
          rounded-lg
          bg-slate-900
          px-5
          py-3
          text-sm
          font-semibold
          text-white
          transition
          hover:bg-slate-700
        "
      >
        {t("Done")}
      </button>
    </div>
  );
}

/* ================= RESULT CARD ================= */

function ResultCard({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-xl bg-slate-50 p-4">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
        {label}
      </p>

      <p className="mt-2 text-2xl font-bold text-slate-900">
        {value}
      </p>
    </div>
  );
}

export default PatientIntake;