from flask import Blueprint, request, jsonify
from datetime import datetime
import json
from db import db

from models.patient import Patient
from models.retriage_alert import RetriageAlert
from models.triage_assessment import TriageAssessment
from models.coordinator_decision import CoordinatorDecision
from models.audit_log import AuditLog
from services.retriage_service import (
    check_retriage_alerts,
    handle_event_driven_retriage,
    handle_manual_esi_override
)


retriage_bp = Blueprint(
    "retriage",
    __name__,
    url_prefix="/api",
)


# ==========================================================
# EVENT-DRIVEN VITAL CHECK
# ==========================================================

@retriage_bp.route(
    "/patients/<int:patient_id>/vitals",
    methods=["POST"],
)
def update_patient_vitals(patient_id):

    try:
        data = request.get_json() or {}

        patient = Patient.query.get(patient_id)

        if not patient:
            return jsonify({
                "error": "Patient not found"
            }), 404

        vitals = data.get("vitals", data)

        allowed_fields = [
            "spo2",
            "bp_systolic",
            "bp_diastolic",
            "heart_rate",
            "temperature",
            "respiratory_rate",
        ]

        previous_vitals = {
            field: getattr(patient, field)
            for field in allowed_fields
        }

        for field in allowed_fields:
            if field in vitals and vitals[field] is not None:
                setattr(patient, field, vitals[field])

        new_vitals = {
            field: getattr(patient, field)
            for field in allowed_fields
        }

        db.session.commit()

        result = handle_event_driven_retriage(
            patient_id,
            "vital_change",
            {
                "previous_vitals": previous_vitals,
                "new_vitals": new_vitals,
            },
        )

        if not result:
            return jsonify({
                "error": "Unable to perform re-triage"
            }), 500

        assessment = result["assessment"]
        triage_assessment = result["triage_assessment"]

        return jsonify({
            "success": True,
            "patient_id": patient.id,
            "assessment_id": triage_assessment.id,

            "previous_vitals": previous_vitals,
            "new_vitals": new_vitals,

            "assessment": {
                "assessment_id": triage_assessment.id,
                "audit_log_id": result["audit_log"].id,
                "esi_level": assessment.get("esi_level"),
                "confidence": assessment.get("confidence"),
                "confidence_band": assessment.get(
                    "confidence_band"
                ),
                "reasoning": assessment.get(
                    "reasoning",
                    [],
                ),
                "auto_escalate_for_review": assessment.get(
                    "auto_escalate_for_coordinator_review",
                    False,
                ),
            },
        }), 200

    except Exception as e:
        db.session.rollback()

        return jsonify({
            "error": str(e)
        }), 500


# ==========================================================
# NEEDS ATTENTION
#
# Includes:
# 1. New patients with an assessment but no decision.
# 2. Triggered time-based re-triage alerts.
# 3. Triggered event-driven re-triage alerts.
#
# A patient can NEVER appear twice.
# ==========================================================

@retriage_bp.route('/retriage-alerts', methods=['GET'])
def get_retriage_alerts():
    """
    Return patients currently requiring coordinator attention.

    There are two cases:

    1. Initial triage:
       Latest assessment has no coordinator decision AND
       there is no active re-triage alert.

    2. Re-triage:
       A triggered RetriageAlert exists and has not yet
       been completed by the coordinator.

    Re-triage always takes priority over initial-review.

    Patients who are already 'in_care' or 'completed' are
    excluded from both cases -- they no longer need to
    appear in the attention queue, even if they have an
    orphaned/undecided assessment or a closed-out alert.
    """

    try:
        attention = []
        seen_patients = set()

        # ==================================================
        # 1. ACTIVE TRIGGERED RETRIAGE ALERTS
        #
        # CHECK THESE FIRST.
        # This prevents a re-triage assessment from being
        # incorrectly labelled "initial-review".
        # ==================================================

        retriage_alerts = (
            RetriageAlert.query
            .join(Patient)
            .filter(
                RetriageAlert.retriaged == False,
                RetriageAlert.alert_triggered == True,
                Patient.status.notin_(["in_care", "completed"]),
            )
            .order_by(
                RetriageAlert.alert_time.desc()
            )
            .all()
        )

        for alert in retriage_alerts:

            patient = Patient.query.get(
                alert.patient_id
            )

            if not patient or patient.status in ("in_care", "completed"):
                continue

            # Never show the same patient twice.
            if patient.id in seen_patients:
                continue

            seen_patients.add(patient.id)

            decision = (
    CoordinatorDecision.query
    .join(
        TriageAssessment,
        CoordinatorDecision.assessment_id == TriageAssessment.id
    )
    .filter(
        TriageAssessment.patient_id == patient.id
    )
    .order_by(
        CoordinatorDecision.id.desc()
    )
    .first()
)

            attention.append({
                "alert_id": alert.id,

                "patient_id": patient.id,

                "esi_level": (
                    decision.coordinator_esi_level
                    if decision
                    else alert.esi_level
                ),

                "arrival_time": (
                    patient.arrival_time.isoformat()
                    if patient.arrival_time
                    else None
                ),

                "wait_time_minutes": (
                    (
                        datetime.utcnow()
                        - patient.arrival_time
                    ).total_seconds() / 60
                    if patient.arrival_time
                    else 0
                ),

                "alert_triggered": True,

                "alert_time": (
                    alert.alert_time.isoformat()
                    if alert.alert_time
                    else None
                ),

                # THIS IS THE IMPORTANT PART
                "alert_type": alert.alert_type,
            })

        # ==================================================
        # 2. INITIAL TRIAGE WAITING FOR FIRST DECISION
        #
        # Only do this if the patient DOES NOT already have
        # an active triggered re-triage alert, AND is not
        # already in_care / completed.
        # ==================================================

        patients = Patient.query.filter(
            Patient.status.notin_(["in_care", "completed"])
        ).all()

        for patient in patients:

            if patient.id in seen_patients:
                continue

            assessment = (
                TriageAssessment.query
                .filter_by(
                    patient_id=patient.id
                )
                .order_by(
                    TriageAssessment.id.desc()
                )
                .first()
            )

            if not assessment:
                continue

            decision = (
                CoordinatorDecision.query
                .filter_by(
                    assessment_id=assessment.id
                )
                .first()
            )

            # Assessment already reviewed.
            if decision:
                continue

            # ------------------------------------------------
            # IMPORTANT:
            #
            # If this patient has an active untriggered
            # monitoring alert, they are already being
            # monitored and should NOT be treated as a
            # brand-new initial review.
            # ------------------------------------------------

            active_alert = (
                RetriageAlert.query
                .filter_by(
                    patient_id=patient.id,
                    retriaged=False,
                    alert_triggered=True,
                )
                .first()
            )

            if active_alert:
                continue

            seen_patients.add(patient.id)

            attention.append({
                "alert_id": f"assessment-{assessment.id}",

                "patient_id": patient.id,

                "esi_level": assessment.ai_esi_level,

                "arrival_time": (
                    patient.arrival_time.isoformat()
                    if patient.arrival_time
                    else None
                ),

                "wait_time_minutes": (
                    (
                        datetime.utcnow()
                        - patient.arrival_time
                    ).total_seconds() / 60
                    if patient.arrival_time
                    else 0
                ),

                "alert_triggered": False,

                "alert_time": None,

                "alert_type": "initial-review",
            })

        return jsonify({
            "alerts": attention
        }), 200

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500

# ==========================================================
# MANUAL RETRIAGE CHECK
# ==========================================================

@retriage_bp.route(
    "/check-retriage",
    methods=["POST"],
)
def manual_retriage_check():

    try:
        triggered = check_retriage_alerts()

        return jsonify({
            "success": True,
            "alerts_triggered": len(triggered),
            "alert_ids": [
                alert.id
                for alert in triggered
            ],
        }), 200

    except Exception as e:

        db.session.rollback()

        return jsonify({
            "error": str(e)
        }), 500


# ==========================================================
# EVENT-DRIVEN RETRIAGE
# ==========================================================

@retriage_bp.route(
    "/event-retriage",
    methods=["POST"],
)
def event_triggered_retriage():

    try:
        data = request.get_json() or {}

        patient_id = data.get("patient_id")
        event_type = data.get("event_type")
        event_data = data.get("data", {})

        if not patient_id or not event_type:
            return jsonify({
                "error": "Missing required fields"
            }), 400

        result = handle_event_driven_retriage(
            patient_id,
            event_type,
            event_data,
        )

        if not result:
            return jsonify({
                "error": "Patient not found"
            }), 404

        assessment = result["assessment"]
        triage_assessment = result["triage_assessment"]

        return jsonify({
            "success": True,
            "assessment_id": triage_assessment.id,
            "audit_log_id": result["audit_log"].id,

            "esi_level": assessment.get(
                "esi_level"
            ),

            "confidence": assessment.get(
                "confidence"
            ),

            "confidence_band": assessment.get(
                "confidence_band"
            ),

            "reasoning": assessment.get(
                "reasoning",
                [],
            ),

            "auto_escalate_for_review": assessment.get(
                "auto_escalate_for_coordinator_review",
                False,
            ),
        }), 200

    except Exception as e:

        db.session.rollback()

        return jsonify({
            "error": str(e)
        }), 500

@retriage_bp.route(
    "/patients/<int:patient_id>/manual-esi",
    methods=["POST"],
)
def manual_esi_override(patient_id):
    """
    Coordinator manually sets an ESI level.

    A manual ESI is immediately coordinator-approved,
    so a CoordinatorDecision is created for the new assessment.
    """

    try:
        # ==========================================================
        # GET DATA FROM FRONTEND
        # ==========================================================

        data = request.get_json() or {}

        esi_level = data.get("esi_level")
        note = data.get("note", "")

        print("========== MANUAL ESI REQUEST ==========")
        print("PATIENT ID:", patient_id)
        print("RAW DATA:", data)
        print("ESI:", esi_level)
        print("ESI TYPE:", type(esi_level))
        print("========================================")

        # ==========================================================
        # VALIDATE ESI
        # ==========================================================

        if esi_level is None:
            return jsonify({
                "error": "esi_level is required"
            }), 400

        try:
            esi_level = int(esi_level)
        except (TypeError, ValueError):
            return jsonify({
                "error": "esi_level must be between 1-5"
            }), 400

        if not 1 <= esi_level <= 5:
            return jsonify({
                "error": "esi_level must be between 1-5"
            }), 400

        # ==========================================================
        # FIND PATIENT
        # ==========================================================

        patient = Patient.query.get(patient_id)

        if not patient:
            return jsonify({
                "error": "Patient not found"
            }), 404

        # ==========================================================
        # CREATE MANUAL ASSESSMENT
        # ==========================================================

        assessment = TriageAssessment(
            patient_id=patient.id,
            ai_esi_level=esi_level,
            ai_confidence=1.0,
            confidence_band="manual",
            ai_reasoning=json.dumps(
                [note] if note else [
                    "Manually set by coordinator"
                ]
            ),
            auto_escalate_for_review=False,
            vital_details=json.dumps({})
        )

        db.session.add(assessment)
        db.session.flush()

        print("========== MANUAL ASSESSMENT ==========")
        print("ASSESSMENT ID:", assessment.id)
        print("ESI:", assessment.ai_esi_level)
        print("CONFIDENCE:", assessment.ai_confidence)
        print("========================================")

        # ==========================================================
        # CREATE COORDINATOR DECISION
        # ==========================================================

        decision = CoordinatorDecision(
            assessment_id=assessment.id,
            coordinator_esi_level=esi_level,
            override_reason=note or "Manual ESI set by coordinator",
            is_override=True
        )

        db.session.add(decision)
        db.session.flush()

        print("========== MANUAL DECISION ==========")
        print("DECISION ID:", decision.id)
        print("COORDINATOR ESI:", decision.coordinator_esi_level)
        print("=====================================")

        # ==========================================================
        # CLOSE OLD RETRIAGE ALERTS
        # ==========================================================

        existing_alerts = RetriageAlert.query.filter_by(
            patient_id=patient.id,
            retriaged=False
        ).all()

        for existing_alert in existing_alerts:
            existing_alert.retriaged = True
            existing_alert.retriage_time = datetime.utcnow()

        # ==========================================================
        # CREATE NEW RETRIAGE ALERT
        # ==========================================================

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

        # ==========================================================
        # AUDIT LOG
        # ==========================================================

        audit_log = AuditLog(
            patient_id=patient_id,
            event_type="manual_override",
            timestamp=datetime.utcnow(),
            ai_esi=None,
            ai_confidence=None,
            coordinator_esi=esi_level,
            coordinator_reasoning=note,
            is_override=True
        )

        db.session.add(audit_log)

        db.session.commit()

        print("========== MANUAL ESI COMPLETE ==========")
        print("PATIENT:", patient_id)
        print("ESI:", esi_level)
        print("ASSESSMENT:", assessment.id)
        print("DECISION:", decision.id)
        print("==========================================")

        # ==========================================================
        # RETURN JSON
        # ==========================================================

        return jsonify({
            "success": True,
            "patient_id": patient_id,
            "esi_level": esi_level,
            "assessment_id": assessment.id,
            "decision_id": decision.id,
            "audit_log_id": audit_log.id,
            "alert_id": alert.id
        }), 200

    except Exception as e:
        db.session.rollback()

        print("========== MANUAL ESI ERROR ==========")
        print(str(e))
        print("======================================")

        return jsonify({
            "error": str(e)
        }), 500