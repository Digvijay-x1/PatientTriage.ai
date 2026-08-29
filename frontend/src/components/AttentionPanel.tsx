import AttentionRow from "./AttentionRow";
import type { RetriageAlert } from "../types/patient";
import { Card } from "./ui/card";
import { useLanguage } from "../context/LanguageContext";

type AttentionPanelProps = {
  alerts: RetriageAlert[];
  onReview: (patientId: string) => void;
};

function AttentionPanel({
  alerts,
  onReview,
}: AttentionPanelProps) {
  const { t } = useLanguage();

  return (
    <section className="mt-4">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-slate-900">
          {t("Needs Attention")}
        </h3>

        <p className="text-sm text-slate-500">
          {t(
            "Patients surfaced by the triage system for coordinator review",
          )}
        </p>
      </div>

      <Card>
        {/* No alerts */}
        {alerts.length === 0 && (
          <div className="p-8 text-center">
            <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-full bg-emerald-50 text-emerald-600">
              ✓
            </div>

            <p className="mt-3 text-sm font-semibold text-slate-800">
              {t("No patients need attention")}
            </p>

            <p className="mt-1 text-xs text-slate-500">
              {t("No active re-triage alerts at the moment.")}
            </p>
          </div>
        )}

        {/* Real alerts */}
        {alerts.map((alert) => (
          <AttentionRow
            key={alert.alert_id}
            patientId={String(alert.patient_id)}
            complaint={
              alert.alert_type === "time-based"
                ? t("Reassessment due")
                : t("Clinical review")
            }
            reason={getAlertReason(alert, t)}
            detail={`${Math.round(alert.wait_time_minutes)} ${t("min waiting")}`}
            status={`ESI-${alert.esi_level}`}
            priority={getPriority(alert.esi_level)}
            onReview={onReview}
          />
        ))}
      </Card>
    </section>
  );
}

function getPriority(
  esiLevel: RetriageAlert["esi_level"],
): "urgent" | "review" {
  return esiLevel <= 2 ? "urgent" : "review";
}

function getAlertReason(
  alert: RetriageAlert,
  t: (text: string) => string,
): string {
  switch (alert.alert_type) {
    case "time-based":
      return t(
        "Patient has reached the scheduled reassessment time.",
      );

    case "event-driven":
      return t(
        "Patient condition requires reassessment.",
      );

    case "initial-review":
      return t(
        "Initial triage assessment requires review.",
      );

    default:
      return t(
        "Patient requires clinical review.",
      );
  }
}

export default AttentionPanel;