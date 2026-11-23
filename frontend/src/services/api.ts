import type {
  CoordinatorDecisionRequest,
  CoordinatorDecisionResponse,
  RetriageAlert,
  RetriageEvent,
  RetriageResponse,
  TriageAssessment,
} from "../types/patient";

// Flask backend URL
const API_BASE_URL = "http://127.0.0.1:5000/api";

async function request<T>(
  endpoint: string,
  options?: RequestInit,
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers || {}),
    },
    ...options,
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.error || "Something went wrong");
  }

  return data;
}


// ======================================
// TRIAGE
// POST /api/triage
// ======================================

export async function runTriage(
  patientId: number,
): Promise<TriageAssessment> {
  return request<TriageAssessment>("/triage", {
    method: "POST",
    body: JSON.stringify({
      patient_id: patientId,
    }),
  });
}


// ======================================
// RE-TRIAGE ALERTS
// GET /api/retriage-alerts
// ======================================

export async function getRetriageAlerts(): Promise<{
  alerts: RetriageAlert[];
}> {
  return request<{ alerts: RetriageAlert[] }>(
    "/retriage-alerts",
  );
}


// ======================================
// EVENT-DRIVEN RE-TRIAGE
// POST /api/event-retriage
// ======================================

export async function triggerRetriage(
  event: RetriageEvent,
): Promise<RetriageResponse> {
  return request<RetriageResponse>("/event-retriage", {
    method: "POST",
    body: JSON.stringify(event),
  });
}


// ======================================
// COORDINATOR DECISION
// POST /api/coordinator-decision
// ======================================

export async function submitCoordinatorDecision(
  decision: CoordinatorDecisionRequest,
): Promise<CoordinatorDecisionResponse> {
  return request<CoordinatorDecisionResponse>(
    "/coordinator-decision",
    {
      method: "POST",
      body: JSON.stringify(decision),
    },
  );
}

export interface RegisterPatientRequest {
  patient_id: string;

  age: number;

  chief_complaint: string;

  sex: string;

  vitals?: {
    spo2?: number;
    bp_systolic?: number;
    bp_diastolic?: number;
    heart_rate?: number;
    temperature?: number;
    pain?: number;
    respiratory_rate?: number;
  };

  observed?: {
    responsiveness?: string;
    breathing?: string;
    distress_level?: string;
  };

  // Medical history
  has_prior_record?: boolean;
  history_cardiac?: boolean;
  history_respiratory?: boolean;
  history_diabetes?: boolean;
  history_renal?: boolean;
  history_hypertension?: boolean;
}

export interface RegisterPatientResponse {
  success: boolean;
  patient_id: number;
  patient_uuid: string;
}

export async function registerPatient(
  patient: RegisterPatientRequest,
): Promise<RegisterPatientResponse> {
  return request<RegisterPatientResponse>("/patients", {
    method: "POST",
    body: JSON.stringify(patient),
  });
}

export async function getPatientAssessment(
  patientId: number,
): Promise<TriageAssessment> {
  return request<TriageAssessment>(
    `/assessments/patient/${patientId}`,
  );
}

export interface WaitingQueuePatient {
  patient_id: number;
  patient_uuid: string;
  age: number;
  chief_complaint: string;
  esi_level: number;
  arrival_time: string;
  wait_time_minutes: number;
  triage_completion_time: string | null;
  assessment_id: number;
  is_override: boolean;
}

export async function getWaitingQueue(): Promise<{
  success: boolean;
  patients: WaitingQueuePatient[];
}> {
  return request<{
    success: boolean;
    patients: WaitingQueuePatient[];
  }>("/waiting-queue");
}

export interface VitalCheckRequest {
  patient_id: number;

  vitals: {
    spo2?: number;
    bp_systolic?: number;
    bp_diastolic?: number;
    heart_rate?: number;
    temperature?: number;
    respiratory_rate?: number;
    pain?: number;
  };
}

export interface VitalCheckResponse {
  success: boolean;
  patient_id: number;

  previous_vitals: Record<string, number | null>;
  new_vitals: Record<string, number | null>;

  assessment: {
    assessment_id: number;
    audit_log_id: number;
    esi_level: number;
    confidence: number;
    confidence_band: string;
    reasoning: string[];
    auto_escalate_for_review: boolean;
  };
}

export async function submitVitalCheck(
  data: VitalCheckRequest,
): Promise<VitalCheckResponse> {
  return request<VitalCheckResponse>(
    `/patients/${data.patient_id}/vitals`,
    {
      method: "POST",
      body: JSON.stringify({
        vitals: data.vitals,
      }),
    },
  );
}

export async function takePatientToCare(
  patientId: number,
) {
  const response = await fetch(
    `http://localhost:5000/api/patients/${patientId}/take-to-care`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
    },
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(
      data.error || "Unable to take patient to care",
    );
  }

  return data;
}

export type InCarePatient = {
  patient_id: number;
  patient_uuid: string;
  age: number;
  chief_complaint: string;
  esi_level: number | null;
  arrival_time: string | null;
  status: string;
};

export async function getInCarePatients(): Promise<{
  success: boolean;
  patients: InCarePatient[];
}> {
  return request<{
    success: boolean;
    patients: InCarePatient[];
  }>("/in-care");
}

export type AuditEvent = {
  id: number;
  patient_id: number;
  event_type: string;
  timestamp: string | null;
  ai_esi: number | null;
  ai_confidence: number | null;
  ai_reasoning: string | null;
  coordinator_esi: number | null;
  coordinator_reasoning: string | null;
  is_override: boolean | null;
};

export async function getAuditTrail(): Promise<{
  success: boolean;
  audit_logs: AuditEvent[];
}> {
  return request<{
    success: boolean;
    audit_logs: AuditEvent[];
  }>("/audit-trail");
}

// ======================================
// PROBLEM REPORTS ON AI RECOMMENDATIONS
// POST /api/incident-reports
// ======================================

export async function reportIncident(payload: {
  patient_id: number | null;
  assessment_id: number | null;
  description: string;
  patient_harmed: boolean;
}): Promise<{
  success: boolean;
  incident_id: number;
  possible_serious_incident: boolean;
}> {
  return request<{
    success: boolean;
    incident_id: number;
    possible_serious_incident: boolean;
  }>("/incident-reports", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function completePatient(
  patientId: number,
): Promise<{
  success: boolean;
  patient_id: number;
  patient_identifier: string;
  status: string;
}> {
  return request<{
    success: boolean;
    patient_id: number;
    patient_identifier: string;
    status: string;
  }>(`/patients/${patientId}/complete`, {
    method: "POST",
  });
}

export async function submitManualEsi(payload: {
  patient_id: number;
  esi_level: number;
  note?: string;
}) {
  console.log("SUBMIT MANUAL ESI PAYLOAD:", payload);

  return request<{
    success: boolean;
    assessment_id: number;
    alert_id: number;
  }>(
    `/patients/${payload.patient_id}/manual-esi`,
    {
      method: "POST",
      body: JSON.stringify({
        esi_level: payload.esi_level,
        note: payload.note,
      }),
    },
  );
}

export async function getAssessmentExplanation(assessmentId: number) {
  const res = await fetch(`/api/assessments/${assessmentId}/explain`);
  if (!res.ok) throw new Error("Failed to load AI explanation");
  return res.json() as Promise<{
    assessment_id: number;
    explanation: string;
  }>;
}