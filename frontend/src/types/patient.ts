
export type EsiLevel = 1 | 2 | 3 | 4 | 5;

export type ConfidenceBand =
  | "high"
  | "medium"
  | "low"
  | "emergency_override";


// -------------------------------
// Patient
// -------------------------------

export interface Patient {
  id: number;

  patient_id?: string;

  age?: number;

  complaint?: string;

  sex?: string;

  // Vital signs
  heart_rate?: number;
  respiratory_rate?: number;
  systolic_bp?: number;
  diastolic_bp?: number;
  spo2?: number;
  temperature?: number;
  pain: number;

  // History
  has_prior_record?: boolean;
  history_cardiac?: boolean;
  history_respiratory?: boolean;
  history_diabetes?: boolean;
  history_renal?: boolean;
  history_hypertension?: boolean;

  // Additional information
  symptoms?: string[];

  arrival_time?: string;
}


// -------------------------------
// AI Triage Assessment
// POST /api/triage
// -------------------------------

export interface TriageAssessment {
  success: boolean;

  assessment_id: number;

  esi_level: EsiLevel;

  confidence: number;

  confidence_band: ConfidenceBand;

  reasoning: string[];

  auto_escalate_for_review: boolean;
}


// -------------------------------
// Re-triage Alert
// GET /api/retriage-alerts
// -------------------------------

export interface RetriageAlert {
  alert_id: number;

  patient_id: number;

  esi_level: EsiLevel;

  arrival_time: string;

  wait_time_minutes: number;

  alert_triggered: boolean;

  alert_time: string | null;

  alert_type: "initial-review" | "time-based" | "event-driven";
}


// -------------------------------
// Event-driven Re-triage
// POST /api/event-retriage
// -------------------------------

export type RetriageEventType =
  | "lab_result"
  | "vital_change"
  | "observation";

export interface RetriageEvent {
  patient_id: number;

  event_type: RetriageEventType;

  data: Record<string, unknown>;
}

export interface RetriageResponse {
  success: boolean;

  audit_log_id: number;

  esi_level: EsiLevel;

  confidence: number;

  confidence_band: ConfidenceBand;

  reasoning: string[];

  auto_escalate_for_review: boolean;
}


// -------------------------------
// Coordinator Decision
// POST /api/coordinator-decision
// -------------------------------

export interface CoordinatorDecisionRequest {
  assessment_id: number;

  coordinator_esi_level: EsiLevel;

  is_override: boolean;

  override_reason?: string;
}

export interface CoordinatorDecisionResponse {
  success: boolean;

  decision_id: number;

  coordinator_esi: EsiLevel;

  is_override: boolean;

  recorded_at: string;
}


// -------------------------------
// API Error
// -------------------------------

export interface ApiError {
  error: string;
}