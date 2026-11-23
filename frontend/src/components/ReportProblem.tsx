import { useState } from "react";
import { reportIncident } from "../services/api";
import { useLanguage } from "../context/LanguageContext";

// Lets a coordinator report a problem with an AI recommendation to the
// provider. Reports where a patient may have been harmed are flagged as a
// possible serious incident (docs/compliance/serious-incident-reporting.md).

type ReportProblemProps = {
  patientId: number | null;
  assessmentId: number | null;
};

function ReportProblem({ patientId, assessmentId }: ReportProblemProps) {
  const { t } = useLanguage();
  const [open, setOpen] = useState(false);
  const [description, setDescription] = useState("");
  const [patientHarmed, setPatientHarmed] = useState(false);
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit() {
    if (!description.trim()) {
      setError(t("Describe what went wrong."));
      return;
    }

    try {
      setSending(true);
      setError(null);

      await reportIncident({
        patient_id: patientId,
        assessment_id: assessmentId,
        description: description.trim(),
        patient_harmed: patientHarmed,
      });

      setSent(true);
      setOpen(false);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : t("Unable to send the report"),
      );
    } finally {
      setSending(false);
    }
  }

  if (sent) {
    return (
      <p className="mt-6 text-sm text-emerald-700">
        {t("Thank you. The report was sent to the provider.")}
      </p>
    );
  }

  return (
    <section className="mt-6">
      {!open ? (
        <button
          type="button"
          onClick={() => setOpen(true)}
          className="text-sm font-medium text-red-700 underline"
        >
          {t("Report a problem with this AI recommendation")}
        </button>
      ) : (
        <div className="rounded-xl border border-red-200 bg-red-50 p-4">
          <label
            htmlFor="incident-description"
            className="text-sm font-semibold text-slate-900"
          >
            {t("What went wrong?")}
          </label>

          <textarea
            id="incident-description"
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            rows={3}
            className="mt-2 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-blue-500"
          />

          <label className="mt-3 flex items-center gap-2 text-sm text-slate-800">
            <input
              type="checkbox"
              checked={patientHarmed}
              onChange={(event) => setPatientHarmed(event.target.checked)}
            />
            {t("A patient was or may have been harmed")}
          </label>

          {error && (
            <p className="mt-2 text-sm text-red-700">{error}</p>
          )}

          <div className="mt-3 flex gap-2">
            <button
              type="button"
              onClick={handleSubmit}
              disabled={sending}
              className="rounded-lg bg-red-700 px-3 py-2 text-sm font-semibold text-white disabled:opacity-50"
            >
              {sending ? t("Sending...") : t("Send report")}
            </button>

            <button
              type="button"
              onClick={() => setOpen(false)}
              className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700"
            >
              {t("Cancel")}
            </button>
          </div>
        </div>
      )}
    </section>
  );
}

export default ReportProblem;
