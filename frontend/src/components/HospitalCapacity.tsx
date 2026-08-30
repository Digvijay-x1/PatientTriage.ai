import { Card } from "./ui/card";
import { useLanguage } from "../context/LanguageContext";
import { hospitalResources } from "../../data/HospitalCapacity";
import type { WaitingQueuePatient } from "../services/api";

type HospitalCapacityProps = {
  patients: WaitingQueuePatient[];
};

function HospitalCapacity({
  patients,
}: HospitalCapacityProps) {
  const { t } = useLanguage();

  // =====================================================
  // ESI COUNTS
  // =====================================================

  const esiCounts = {
    1: patients.filter((p) => p.esi_level === 1).length,
    2: patients.filter((p) => p.esi_level === 2).length,
    3: patients.filter((p) => p.esi_level === 3).length,
    4: patients.filter((p) => p.esi_level === 4).length,
    5: patients.filter((p) => p.esi_level === 5).length,
  };

  const esiLabels: Record<number, string> = {
    1: "Immediate",
    2: "Emergent",
    3: "Urgent",
    4: "Less urgent",
    5: "Non-urgent",
  };

  return (
    <section className="mt-6">

      {/* ================================================= */}
      {/* HOSPITAL CAPACITY */}
      {/* ================================================= */}

      <div className="mb-4">
        <h3 className="text-lg font-semibold text-slate-900">
          {t("Hospital Capacity")}
        </h3>

        <p className="text-sm text-slate-500">
          {t("Current availability of hospital resources")}
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">

        {hospitalResources.map((resource) => {

          const occupied =
            resource.total - resource.available;

          const occupancy =
            Math.round(
              (occupied / resource.total) * 100
            );

          return (
            <Card
              key={resource.name}
              className="p-5"
            >

              <p className="text-sm font-medium text-slate-900">
                {t(resource.name)}
              </p>

              <div className=" flex items-end gap-2">

                <span className="text-2xl font-bold text-slate-900">
                  {resource.available}
                </span>

                <span className="mb-1 text-sm text-slate-400">
                  / {resource.total}
                </span>

              </div>

              <p className="text-xs text-slate-500">
                {t("available")}
              </p>

              <div className=" h-2 overflow-hidden rounded-full bg-slate-100">

                <div
                  className="h-full rounded-full bg-blue-500"
                  style={{
                    width: `${occupancy}%`,
                  }}
                />

              </div>

              <p className="text-xs text-slate-400">
                {occupancy}% {t("occupied")}
              </p>

            </Card>
          );
        })}

      </div>

      {/* ================================================= */}
      {/* TRIAGE LOAD */}
      {/* ================================================= */}

      <div className="mb-4 mt-8">

        <h3 className="text-lg font-semibold text-slate-900">
          {t("Triage Load")}
        </h3>

        <p className="text-sm text-slate-500">
          {t("Current patients by ESI level")}
        </p>

      </div>

      <Card className="overflow-hidden p-0">

        {[1, 2, 3, 4, 5].map((esi) => {

          const count =
            esiCounts[
              esi as 1 | 2 | 3 | 4 | 5
            ];

          return (
            <div
              key={esi}
              className="flex items-center justify-between border-b border-slate-100 px-5 py-4 last:border-b-0"
            >

              <div className="flex items-center gap-4">

                <span className="w-14 text-sm font-semibold text-slate-900">
                  ESI-{esi}
                </span>

                <span className="text-sm text-slate-500">
                  {t(esiLabels[esi])}
                </span>

              </div>

              <span className="text-sm font-semibold text-slate-900">
                {count}{" "}
                {count === 1
                  ? t("patient")
                  : t("patients")}
              </span>

            </div>
          );
        })}

      </Card>

    </section>
  );
}

export default HospitalCapacity;