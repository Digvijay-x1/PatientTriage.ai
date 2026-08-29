import { useEffect, useRef, useState } from "react";

import StatCard from "../components/StatCard";
import AttentionPanel from "../components/AttentionPanel";
import PatientQueue from "../components/PatientQueue";
import PatientReview from "../components/PatientReview";
import PatientIntake from "../components/PatientIntake";
import { Button } from "../components/ui/button";
import { getRetriageAlerts , getInCarePatients, type InCarePatient, getAuditTrail, type AuditEvent, completePatient} from "../services/api";
import { toast } from "../components/ui/toast";
import { useLanguage } from "../context/LanguageContext";

import {
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
} from "../components/ui/tabs";

import type { RetriageAlert } from "../types/patient";

function Dashboard() {
  const [alerts, setAlerts] = useState<RetriageAlert[]>([]);
  const [loadingAlerts, setLoadingAlerts] = useState(true);

  const [selectedPatientId, setSelectedPatientId] =
    useState<string | null>(null);

  const [queueRefreshKey, setQueueRefreshKey] = useState(0);
  const [alertRefreshKey, setAlertRefreshKey] = useState(0);
  const [showPatientIntake, setShowPatientIntake] = useState(false);

  const [inCarePatients, setInCarePatients] = useState<InCarePatient[]>([]);
const [loadingInCare, setLoadingInCare] = useState(true);

const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);
const [loadingAudit, setLoadingAudit] = useState(true);
  // Prevent the same time-based alert from showing
  // the toast repeatedly.
  const shownToastAlerts = useRef<Set<number | string>>(
    new Set(),
  );
  const { language, setLanguage, t } = useLanguage();


  useEffect(() => {
    let isFirstLoad =true;
  async function loadAuditTrail() {
    try {
      if (isFirstLoad) {
        setLoadingAudit(true);
      }

      const data = await getAuditTrail();

      setAuditEvents(data.audit_logs);
    } catch (error) {
      console.error(
        "Failed to load audit trail:",
        error,
      );
    } finally {
     if (isFirstLoad) {
        setLoadingAudit(false);
        isFirstLoad = false;
      }
    }
  }

  loadAuditTrail();

  const interval = setInterval(
    loadAuditTrail,
    10000,
  );

  return () => clearInterval(interval);
}, []);

  useEffect(() => {
    let isFirstLoad = true;
  async function loadInCarePatients() {
    try {
      if (isFirstLoad) {
        setLoadingInCare(true);
      }

      const data = await getInCarePatients();

      setInCarePatients(data.patients);
    } catch (error) {
      console.error(
        "Failed to load in-care patients:",
        error,
      );
    }  if (isFirstLoad) {
        setLoadingInCare(false);
        isFirstLoad = false;
      }
  }

  loadInCarePatients();

  const interval = setInterval(
    loadInCarePatients,
    10000,
  );

  return () => clearInterval(interval);
}, []);
  // ==========================================================
  // LOAD ALERTS
  // ==========================================================

useEffect(() => {
  let isFirstLoad = true;

  async function loadAlerts() {
    try {
      if (isFirstLoad) {
        setLoadingAlerts(true);
      }
      const data = await getRetriageAlerts();
      setAlerts(data.alerts);
    } catch (error) {
      console.error("Failed to load re-triage alerts:", error);
    } finally {
      if (isFirstLoad) {
        setLoadingAlerts(false);
        isFirstLoad = false;
      }
    }
  }

  loadAlerts();

  const interval = setInterval(loadAlerts, 10000);

  return () => clearInterval(interval);
}, [alertRefreshKey]);

  useEffect(() => {
  const interval = setInterval(async () => {
    try {
      const response = await fetch(
        "http://127.0.0.1:5000/api/check-retriage",
        {
          method: "POST",
        },
      );

      const data = await response.json();

      console.log(
        "[RE-TRIAGE CHECK]",
        data,
      );
    } catch (error) {
      console.error(
        "[RE-TRIAGE CHECK ERROR]",
        error,
      );
    }
  }, 10000);

  return () => clearInterval(interval);
}, []);
  // ==========================================================
  // AUTO-REFRESH WAITING QUEUE
  // ==========================================================

  useEffect(() => {
    const interval = setInterval(() => {
      setQueueRefreshKey((current) => current + 1);
    }, 10000);

    return () => clearInterval(interval);
  }, []);

 
  // ==========================================================
  // TIME-BASED RETRIAGE TOAST
  //
  // Only time-based triggered alerts show a toast.
  // ==========================================================

  useEffect(() => {
    alerts.forEach((alert) => {
      if (alert.alert_type !== "time-based") {
        return;
      }

      if (!alert.alert_triggered) {
        return;
      }

      if (
        shownToastAlerts.current.has(alert.alert_id)
      ) {
        return;
      }

      shownToastAlerts.current.add(alert.alert_id);

      toast.add({
        title: "Re-triage due",
        description: `Patient P${String(
          alert.patient_id,
        ).padStart(3, "0")} has reached the reassessment threshold.`,
        type: "warning",
      });
    });
  }, [alerts]);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">

  {/* ======================================================
      TABS ROOT
      ====================================================== */}

  <Tabs
    defaultValue="overview"
    className="w-full"
  >

    {/* ====================================================
        HEADER
        ==================================================== */}

    <header className="border-b border-slate-200 bg-white">

      <div className="mx-auto w-full max-w-7xl px-6">

        {/* =================================================
            TOP ROW
            ================================================= */}

        <div className="flex w-full items-center justify-between py-4">

          {/* Brand - LEFT */}
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">
              PatientTriage
              <span className="text-blue-600">
                .ai
              </span>
            </h1>

            <div className="mt-0.5 flex items-center gap-2">
              <span className="h-1 w-1 rounded-full bg-slate-300" />

              <p className="text-xs font-medium tracking-wide text-slate-500">
                {t("EMERGENCY DEPARTMENT COORDINATION")}
              </p>
            </div>
          </div>

          <div className="flex shrink-0 items-center gap-4">

            {/* Language */}
            <select
              value={language}
              onChange={(e) =>
                setLanguage(e.target.value as "en" | "hi")
              }
              className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs font-medium text-slate-700 outline-none focus:border-blue-500"
            >
              <option value="en">English</option>
              <option value="hi">हिन्दी</option>
            </select>

            {/* ED Live */}
            <div className="flex items-center gap-2">
              <span className="h-3 w-3 animate-pulse rounded-full bg-emerald-500" />

              <span className="text-sm font-semibold text-emerald-700">
                {t("ED Live")}
              </span>
            </div>

          </div>

        </div>

        {/* =================================================
            NAVIGATION TABS
            ================================================= */}

        <div className="border-t border-slate-100">

          <TabsList
            variant="line"
            className="h-12 w-full justify-start gap-6 rounded-none p-0"
          >

            <TabsTrigger
              value="overview"
              className="flex-none px-1"
            >
              {t("Overview")}
            </TabsTrigger>

            <TabsTrigger
              value="attention"
              className="flex-none px-1"
            >
              {t("Needs Attention")}
            </TabsTrigger>

            <TabsTrigger
              value="waiting"
              className="flex-none px-1"
            >
              {t("Waiting Queue")}
            </TabsTrigger>

            <TabsTrigger
              value="in-care"
              className="flex-none px-1"
            >
              {t("In Care")}
            </TabsTrigger>

            <TabsTrigger
              value="audit"
              className="flex-none px-1"
            >
              {t("Audit Trail")}
            </TabsTrigger>

          </TabsList>

        </div>

      </div>

    </header>


    {/* ====================================================
        MAIN CONTENT
        ==================================================== */}

    <main className="w-full py-6">
      <div className="mx-auto max-w-7xl px-6">

        <TabsContent
          value="overview"
          className="mt-0"
        >

          {/* Page heading */}
          <div className="mb-5">

            <h2 className="text-xl font-bold tracking-tight">
              {t("Emergency Department Overview")}
            </h2>

            <p className="mt-1 text-slate-500">
              {t("Focus your attention where it matters most.")}
            </p>

          </div>


          {/* Add Patient */}
          <div className="mb-6 flex">

            <Button
              onClick={() =>
                setShowPatientIntake(true)
              }
            >
              + {t("Add Patient")}
            </Button>

          </div>


          {/* =================================================
              STATS
              ================================================= */}

          <div className="grid grid-cols-1 gap-4 py-2 sm:grid-cols-2 lg:grid-cols-4">

            <StatCard
              label={t("Re-triage")}
              value={
                loadingAlerts
                  ? "..."
                  : String(alerts.length)
              }
              description={t("Reassessment required")}
            />

            <StatCard
              label={t("ED Capacity")}
              value="87%"
              description={t("Current utilization")}
            />

          </div>


            {/* =================================================
                NEEDS ATTENTION + WAITING QUEUE
                ORIGINAL SIDE-BY-SIDE LAYOUT
                ================================================= */}

            <div className="mt-4 grid grid-cols-1 items-stretch gap-6 lg:grid-cols-2">

              <AttentionPanel
                alerts={alerts}
                onReview={(patientId) =>
                  setSelectedPatientId(patientId)
                }
              />

              <PatientQueue
                refreshKey={queueRefreshKey}
                onRetriageTriggered={() =>
                  setAlertRefreshKey(
                    (current) => current + 1,
                  )
                }
              />

            </div>

          </TabsContent>


          {/* ==================================================
              NEEDS ATTENTION
              ================================================== */}

          <TabsContent
            value="attention"
            className="mt-0"
          >

            <AttentionPanel
              alerts={alerts}
              onReview={(patientId) =>
                setSelectedPatientId(patientId)
              }
            />

          </TabsContent>


          {/* ==================================================
              WAITING QUEUE
              ================================================== */}

          <TabsContent
            value="waiting"
            className="mt-0"
          >

            <PatientQueue
              refreshKey={queueRefreshKey}
              onRetriageTriggered={() =>
                setAlertRefreshKey(
                  (current) => current + 1,
                )
              }
            />

          </TabsContent>


          {/* ==================================================
              IN CARE
              ================================================== */}
<TabsContent
  value="in-care"
  className="mt-0"
>
  <section className="mt-8">

    <div className="mb-4">
      <h2 className="text-xl font-bold tracking-tight">
        In Care
      </h2>

      <p className="mt-1 text-slate-500">
        Patients currently receiving treatment.
      </p>
    </div>

    {loadingInCare ? (

      <div className="rounded-xl border border-slate-200 bg-white p-8 shadow-sm">
        <p className="text-sm text-slate-500">
          Loading patients in care...
        </p>
      </div>

    ) : inCarePatients.length === 0 ? (

      <div className="flex min-h-[240px] items-center justify-center rounded-xl border border-slate-200 bg-white p-8 text-center shadow-sm">

        <div>
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-slate-100 text-slate-500">
            ✓
          </div>

          <p className="mt-4 text-sm font-semibold text-slate-800">
            No patients currently in care
          </p>

          <p className="mt-1 text-sm text-slate-500">
            Patients will appear here when they are moved into care.
          </p>
        </div>

      </div>

    ) : (

      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">

        {/* Header */}
        <div className="hidden grid-cols-12 border-b border-slate-100 bg-slate-50 px-5 py-3 text-xs font-semibold uppercase tracking-wide text-slate-500 sm:grid">

          <div className="col-span-2">
            Patient
          </div>

          <div className="col-span-3">
            Complaint
          </div>

          <div className="col-span-2">
            Priority
          </div>

          <div className="col-span-2">
            Status
          </div>

          <div className="col-span-1 text-right">
            Arrival
          </div>

          <div className="col-span-2 text-right">
            Action
          </div>

        </div>

        {/* Patients */}
        {inCarePatients.map((patient) => (

          <div
            key={patient.patient_id}
            className="grid grid-cols-1 gap-4 border-b border-slate-100 px-5 py-5 last:border-b-0 sm:grid-cols-12 sm:items-center"
          >

            {/* Patient */}
            <div className="sm:col-span-2">
              <p className="font-semibold text-slate-900">
                {patient.patient_uuid}
              </p>
            </div>

            {/* Complaint */}
            <div className="sm:col-span-3">
              <p className="text-sm text-slate-700">
                {patient.chief_complaint}
              </p>
            </div>

            {/* Priority */}
            <div className="sm:col-span-2">
              {patient.esi_level ? (
                <span className="inline-flex rounded-full bg-orange-100 px-3 py-1 text-xs font-semibold text-orange-700">
                  ESI-{patient.esi_level}
                </span>
              ) : (
                <span className="text-sm text-slate-400">
                  —
                </span>
              )}
            </div>

            {/* Status */}
            <div className="sm:col-span-2">
              <span className="inline-flex rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-700">
                In Care
              </span>
            </div>

            {/* Arrival */}
            <div className="text-sm text-slate-500 sm:col-span-1 sm:text-right">
              {patient.arrival_time
                ? new Date(
                    patient.arrival_time,
                  ).toLocaleTimeString([], {
                    hour: "2-digit",
                    minute: "2-digit",
                  })
                : "—"}
            </div>

            {/* Complete */}
            <div className="sm:col-span-2 sm:text-right">
              <Button
                variant="outline"
                size="sm"
                onClick={async () => {
                  try {
                    await completePatient(
                      patient.patient_id,
                    );

                    setInCarePatients((current) =>
                      current.filter(
                        (p) =>
                          p.patient_id !==
                          patient.patient_id,
                      ),
                    );

                    setQueueRefreshKey(
                      (current) => current + 1,
                    );

                  } catch (error) {
                    console.error(
                      "Failed to complete patient:",
                      error,
                    );
                  }
                }}
              >
                Complete
              </Button>
            </div>

          </div>

        ))}

      </div>

    )}

  </section>
</TabsContent>


   <TabsContent
  value="audit"
  className="mt-0 w-full"
>
  <section className="w-full">

    <div className="mb-6">
      <h2 className="text-xl font-bold tracking-tight">
        {t("Audit Trail")}
      </h2>

      <p className="mt-1 text-slate-500">
        {t("Clinical decisions, overrides, and re-triage events.")}
      </p>
    </div>

    {loadingAudit ? (

      <div className="w-full rounded-xl border border-slate-200 bg-white p-8 shadow-sm">
        <p className="text-sm text-slate-500">
          {t("Loading audit trail...")}
        </p>
      </div>

    ) : auditEvents.length === 0 ? (

      <div className="flex min-h-[240px] w-full items-center justify-center rounded-xl border border-slate-200 bg-white p-8 text-center shadow-sm">
        <div>
          <p className="text-sm font-semibold text-slate-800">
            {t("No audit events yet")}
          </p>

          <p className="mt-1 text-sm text-slate-500">
            {t("Clinical actions will appear here.")}
          </p>
        </div>
      </div>

    ) : (

      <div className="w-full overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">

        {/* Table header */}
        <div className="hidden grid-cols-12 border-b border-slate-100 bg-slate-50 px-6 py-3 text-xs font-semibold uppercase tracking-wide text-slate-500 sm:grid">

          <div className="col-span-2">
            {t("Patient")}
          </div>

          <div className="col-span-3">
            {t("Event")}
          </div>

          <div className="col-span-2">
            {t("AI ESI")}
          </div>

          <div className="col-span-2">
            {t("Coordinator")}
          </div>

          <div className="col-span-3 text-right">
            {t("Time")}
          </div>

        </div>

        {/* Audit events */}
        {auditEvents.map((event) => (

          <div
            key={event.id}
            className="grid grid-cols-1 gap-3 border-b border-slate-100 px-6 py-5 last:border-b-0 sm:grid-cols-12 sm:items-center"
          >

            {/* Patient */}
            <div className="sm:col-span-1">
              <span className="font-semibold text-slate-900">
                P{String(event.patient_id).padStart(3, "0")}
              </span>
            </div>

            {/* Event */}
            <div className="sm:col-span-4">
              <p className="text-sm font-medium text-slate-800">
                {t(formatAuditEvent(event.event_type))}
              </p>

              {event.is_override && (
                <span className="mt-1 inline-flex rounded-full bg-orange-100 px-2 py-0.5 text-[11px] font-semibold text-orange-700">
                  {t("Override")}
                </span>
              )}
            </div>

            {/* AI ESI */}
            <div className="sm:col-span-2">
              {event.ai_esi ? (
                <span className="text-sm font-medium text-slate-700">
                  ESI-{event.ai_esi}
                </span>
              ) : (
                <span className="text-sm text-slate-400">
                  —
                </span>
              )}
            </div>

            {/* Coordinator */}
            <div className="sm:col-span-2">
              {event.coordinator_esi ? (
                <span
                  className={
                    event.is_override
                      ? "text-sm font-semibold text-orange-600"
                      : "text-sm font-medium text-slate-700"
                  }
                >
                  ESI-{event.coordinator_esi}
                </span>
              ) : (
                <span className="text-sm text-slate-400">
                  —
                </span>
              )}
            </div>

            {/* Timestamp */}
            <div className="text-right text-xs text-slate-500 sm:col-span-3">
              {event.timestamp
                ? new Date(
                    event.timestamp,
                  ).toLocaleString()
                : "—"}
            </div>

          </div>

        ))}

      </div>

    )}

  </section>
</TabsContent>
  </div>
        </main>


        {/* ====================================================
            PATIENT INTAKE
            GLOBAL, SO IT WORKS FROM ANY TAB
            ==================================================== */}

        <PatientIntake
          open={showPatientIntake}
          onPatientAdded={() => {
            setAlertRefreshKey(
              (current) => current + 1,
            );

            setQueueRefreshKey(
              (current) => current + 1,
            );
          }}
          onClose={() =>
            setShowPatientIntake(false)
          }
        />


        {/* ====================================================
            PATIENT REVIEW
            GLOBAL, SO IT WORKS FROM ANY TAB
            ==================================================== */}

        {selectedPatientId && (
          <PatientReview
            patientId={selectedPatientId}

            onClose={() =>
              setSelectedPatientId(null)
            }

            onDecisionComplete={() => {

              // Remove patient from Needs Attention
              setAlerts((currentAlerts) =>
                currentAlerts.filter(
                  (alert) =>
                    String(alert.patient_id) !==
                    selectedPatientId,
                ),
              );

              // Refresh Waiting Queue
              setQueueRefreshKey(
                (current) => current + 1,
              );

              // Close review
              setSelectedPatientId(null);
            }}
          />
        )}

      </Tabs>
  
    </div>
  );
}

function formatAuditEvent(eventType: string): string {
  switch (eventType) {
    case "confirmation":
      return "Coordinator confirmed";

    case "override":
      return "Coordinator override";

    case "retriage_assessment":
      return "Re-triage assessment";

    case "taken_to_care":
      return "Patient taken to care";

    case "alert":
      return "Re-triage alert";

    default:
      return eventType;
  }
}

export default Dashboard;