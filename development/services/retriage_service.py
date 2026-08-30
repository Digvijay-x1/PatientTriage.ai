# Re-triage monitoring logic

from datetime import datetime, timedelta
import json

from db import db
from models.patient import Patient
from models.retriage_alert import RetriageAlert
from models.audit_log import AuditLog
from models.triage_assessment import TriageAssessment


# ESI-level specific wait thresholds, in minutes
RETRIAGE_THRESHOLDS = {
    1: 0,
    2: 15,
    3: 30,
    4: 60,
    5: 90,
}


def create_retriage_monitoring(patient_id, esi_level):
    """
    Start a fresh time-based re-triage monitoring cycle.

    The timer starts NOW, immediately after the
    coordinator's latest decision.
    """

    patient = Patient.query.get(patient_id)

    if not patient:
        return None

    esi_level = int(esi_level)

    threshold_minutes = RETRIAGE_THRESHOLDS.get(
        esi_level,
        30,
    )

    # --------------------------------------------------
    # Close any existing active monitoring timers
    # --------------------------------------------------

    existing_alerts = (
        RetriageAlert.query
        .filter_by(
            patient_id=patient_id,
            retriaged=False,
        )
        .all()
    )

    now = datetime.utcnow()

    for existing_alert in existing_alerts:
        existing_alert.retriaged = True
        existing_alert.retriage_time = now

    # --------------------------------------------------
    # Start NEW timer using the NEW coordinator ESI
    # --------------------------------------------------

    next_check = (
        now
        + timedelta(minutes=threshold_minutes)
    )

    alert = RetriageAlert(
        patient_id=patient_id,
        esi_level=esi_level,

        # Original arrival time stays unchanged.
        arrival_time=patient.arrival_time,

        # Timer starts from coordinator decision.
        next_recheck_time=next_check,

        alert_type="time-based",
        alert_triggered=False,
        retriaged=False,
    )

    db.session.add(alert)

    return alert

def check_retriage_alerts():
    """
    Check pending time-based re-triage alerts.

    When an alert triggers:
    1. Mark the alert as triggered.
    2. Generate a NEW AI triage assessment.
    3. Store that assessment.
    4. Create an audit entry.
    5. Surface the patient for coordinator review.

    Runs periodically, e.g. every 30 seconds.
    """

    from services.triage_service import run_triage_assessment

    pending_alerts = (
        RetriageAlert.query
        .join(Patient)
        .filter(
            RetriageAlert.retriaged == False,
            RetriageAlert.alert_triggered == False,
            Patient.status == "waiting",
        )
        .all()
    )

    triggered_alerts = []

    for alert in pending_alerts:

        print(
    "[RE-TRIAGE CHECK]",
    "alert_id=", alert.id,
    "patient_id=", alert.patient_id,
    "esi=", alert.esi_level,
    "next_check=", alert.next_recheck_time,
    "now=", datetime.utcnow(),
)

        if not alert.should_trigger():
            continue


        print(
            "[RE-TRIAGE TRIGGERING]",
            "alert_id=", alert.id,
            "patient_id=", alert.patient_id,
            "esi=", alert.esi_level,
        )
        patient = Patient.query.get(alert.patient_id)

        if not patient:
            continue

        # --------------------------------------------------
        # 1. Mark the time-based alert as triggered
        # --------------------------------------------------

        alert.alert_triggered = True
        alert.alert_time = datetime.utcnow()

        # --------------------------------------------------
        # 2. Generate a NEW AI assessment
        #
        # This is critical.
        # We do NOT reuse the old assessment because it
        # already has a coordinator decision.
        # --------------------------------------------------

        assessment_result = run_triage_assessment(
            patient,
            event_context={
                "event_type": "time-based-retriage",
                "data": {
                    "wait_time_minutes": (
                        datetime.utcnow()
                        - patient.arrival_time
                    ).total_seconds() / 60,

                    "previous_esi_level": alert.esi_level,
                },
            },
        )

        alert.esi_level =  assessment_result["esi_level"]

        # --------------------------------------------------
        # 3. Save NEW TriageAssessment
        # --------------------------------------------------

        assessment = TriageAssessment(
            patient_id=patient.id,

            ai_esi_level=assessment_result["esi_level"],

            ai_confidence=assessment_result["confidence"],

            confidence_band=assessment_result[
                "confidence_band"
            ],

            ai_reasoning=json.dumps(
                assessment_result.get(
                    "reasoning",
                    []
                )
            ),

            auto_escalate_for_review=assessment_result.get(
                "auto_escalate_for_coordinator_review",
                False,
            ),

            vital_details=json.dumps({}),
        )

        db.session.add(assessment)
        db.session.flush()

        # --------------------------------------------------
        # 4. Audit the time-based re-triage
        # --------------------------------------------------

        audit_log = AuditLog(
            patient_id=patient.id,

            event_type="retriage_assessment",

            timestamp=datetime.utcnow(),

            ai_esi=assessment_result["esi_level"],

            ai_confidence=assessment_result["confidence"],

            ai_reasoning=json.dumps(
                assessment_result.get(
                    "reasoning",
                    []
                )
            ),

            retriage_reason="time-based",
        )

        db.session.add(audit_log)

        # --------------------------------------------------
        # 5. Keep the alert active for coordinator review
        #
        # Do NOT set retriaged=True here.
        #
        # It should become retriaged=True only after the
        # coordinator actually confirms/overrides the NEW
        # assessment.
        # --------------------------------------------------

        triggered_alerts.append(alert)

    # ------------------------------------------------------
    # Commit all triggered alerts + new assessments
    # ------------------------------------------------------

    if triggered_alerts:
        db.session.commit()

    return triggered_alerts

def handle_event_driven_retriage(
    patient_id,
    event_type,
    data,
):
    """
    Run a fresh V2 assessment after a clinical event.
    """

    from services.triage_service import run_triage_assessment

    patient = Patient.query.get(patient_id)

    if not patient:
        return None

    # =====================================================
    # RUN FRESH ASSESSMENT
    # =====================================================

    assessment_result = run_triage_assessment(
        patient,
        event_context={
            "event_type": event_type,
            "data": data,
        },
    )

    # =====================================================
    # CREATE NEW TRIAGE ASSESSMENT
    # =====================================================

    assessment = TriageAssessment(
        patient_id=patient.id,

        ai_esi_level=assessment_result["esi_level"],

        ai_confidence=(
            assessment_result["confidence"]
            if assessment_result["confidence"] is not None
            else 0.0
        ),

        confidence_band=assessment_result.get(
            "confidence_band"
        ),

        ai_reasoning=json.dumps(
            assessment_result.get(
                "reasoning",
                [],
            )
        ),

        auto_escalate_for_review=assessment_result.get(
            "auto_escalate_for_coordinator_review",
            False,
        ),

        vital_details=json.dumps(
            data.get(
                "new_vitals",
                {},
            )
        ),
    )

    db.session.add(assessment)

    db.session.flush()

    # =====================================================
    # CLOSE OLD ALERTS
    # =====================================================

    existing_alerts = (
        RetriageAlert.query
        .filter_by(
            patient_id=patient.id,
            retriaged=False,
        )
        .all()
    )

    for existing_alert in existing_alerts:

        existing_alert.retriaged = True
        existing_alert.retriage_time = datetime.utcnow()

    # =====================================================
    # CREATE NEW ALERT
    # =====================================================

    alert = RetriageAlert(
        patient_id=patient.id,

        esi_level=assessment_result["esi_level"],

        arrival_time=patient.arrival_time,

        next_recheck_time=datetime.utcnow(),

        alert_type="event-driven",

        alert_triggered=True,

        alert_time=datetime.utcnow(),

        retriaged=False,
    )

    db.session.add(alert)

    # =====================================================
    # AUDIT
    # =====================================================

    audit_log = AuditLog(
        patient_id=patient_id,

        event_type="retriage_assessment",

        timestamp=datetime.utcnow(),

        ai_esi=assessment_result["esi_level"],

        ai_confidence=(
            assessment_result["confidence"]
            if assessment_result["confidence"] is not None
            else 0.0
        ),

        ai_reasoning=json.dumps(
            assessment_result.get(
                "reasoning",
                [],
            )
        ),

        retriage_reason=(
            f"event-driven: {event_type}"
        ),
    )

    db.session.add(audit_log)

    db.session.commit()

    return {
        "audit_log": audit_log,
        "assessment": assessment_result,
        "triage_assessment": assessment,
        "alert": alert,
    }
def complete_retriage(
    patient_id,
    new_esi_level,
    assessment_id=None,
):
    """
    Complete the re-triage alert associated with the
    coordinator's current assessment.

    The old alert is stopped here.
    A new monitoring cycle is started separately
    after the coordinator decision is committed.
    """

    alerts = (
        RetriageAlert.query
        .filter_by(
            patient_id=patient_id,
            retriaged=False,
        )
        .order_by(
            RetriageAlert.alert_time.desc()
        )
        .all()
    )

    completed_alert = None

    for alert in alerts:

        # Only complete an alert that has actually
        # triggered and is waiting for coordinator review.
        if not alert.alert_triggered:
            continue

        alert.retriaged = True
        alert.retriage_time = datetime.utcnow()
        alert.new_esi_level = int(new_esi_level)

        completed_alert = alert

        # Only one active triggered alert should be
        # completed for this decision.
        break

    return completed_alert

def handle_manual_esi_override(patient_id, esi_level, note=""):
    """
    Coordinator manually sets an ESI level with no AI involved.
    Creates a pending assessment that still requires a
    coordinator-decision to close out, same as every other path.
    """
    patient = Patient.query.get(patient_id)
    if not patient:
        return None


    print("========== MANUAL ESI DEBUG ==========")
    print("ESI:", esi_level)
    print("MANUAL CONFIDENCE:", 1.0)
    print("======================================")
    assessment = TriageAssessment(
    patient_id=patient.id,
    ai_esi_level=esi_level,
    confidence_band="manual",
    ai_reasoning=json.dumps(
        [note] if note else ["Manually set by coordinator"]
    ),
    auto_escalate_for_review=True,
    vital_details=json.dumps({}),
)

    assessment.ai_confidence = 1.0
    print("========== ASSESSMENT OBJECT ==========")
    print("ai_esi_level:", assessment.ai_esi_level)
    print("ai_confidence:", assessment.ai_confidence)
    print("confidence_band:", assessment.confidence_band)
    print("OBJECT DICT:", assessment.__dict__)
    print("=======================================")
    db.session.add(assessment)
    db.session.flush()

    existing_alerts = RetriageAlert.query.filter_by(
        patient_id=patient.id, retriaged=False
    ).all()
    for existing_alert in existing_alerts:
        existing_alert.retriaged = True
        existing_alert.retriage_time = datetime.utcnow()

    alert = RetriageAlert(
        patient_id=patient.id,
        esi_level=esi_level,
        arrival_time=patient.arrival_time,
        next_recheck_time=datetime.utcnow(),
        alert_type="manual-override",
        alert_triggered=True,
        alert_time=datetime.utcnow(),
        retriaged=False,
    )
    db.session.add(alert)

    audit_log = AuditLog(
        patient_id=patient_id,
        event_type="manual_override_request",
        timestamp=datetime.utcnow(),
        ai_esi=None,
        ai_confidence=1.0,
        coordinator_esi=esi_level,
        coordinator_reasoning=note,
        is_override=True,
    )
    db.session.add(audit_log)

    db.session.commit()

    return {"audit_log": audit_log, "assessment": assessment, "alert": alert}