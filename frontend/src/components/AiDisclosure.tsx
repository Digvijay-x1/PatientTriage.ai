import { useLanguage } from "../context/LanguageContext";

// Tells the coordinator, before any interaction, that the triage
// recommendations come from an AI system. Always rendered, never dismissible.
// The compact form is used inside dialogs that show model output, because a
// dialog covers the page banner.

type AiDisclosureProps = {
  compact?: boolean;
};

function AiDisclosure({ compact = false }: AiDisclosureProps) {
  const { t } = useLanguage();

  return (
    <div
      role="note"
      aria-label={t("AI system notice")}
      className={`flex items-start gap-3 rounded-xl border border-amber-300 bg-amber-50 text-slate-900 ${
        compact ? "my-3 px-3 py-2" : "my-4 px-4 py-3"
      }`}
    >
      <span
        role="img"
        aria-label={t("AI system")}
        className="inline-flex h-7 min-w-7 shrink-0 items-center justify-center rounded-md bg-blue-700 px-1.5 text-xs font-bold text-white"
      >
        AI
      </span>

      <div>
        <p className="text-sm font-semibold">
          {t("You are interacting with an AI system, not a person.")}
        </p>

        {!compact && (
          <p className="mt-1 text-sm text-slate-800">
            {t(
              "The ESI recommendations in PatientTriage.ai come from a machine-learning model. A coordinator checks every recommendation and decides the patient's priority.",
            )}
          </p>
        )}
      </div>
    </div>
  );
}

export default AiDisclosure;
