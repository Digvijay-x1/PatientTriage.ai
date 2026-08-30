# POST /api/coordinator-decision (confirm/override)
from flask import Blueprint, request, jsonify
from datetime import datetime
import json


from models.triage_assessment import TriageAssessment
from models.coordinator_decision import CoordinatorDecision
from models.audit_log import AuditLog
from db import db
from services.retriage_service import (
    complete_retriage,
    create_retriage_monitoring,
)
from models.patient import Patient
from models.retriage_alert import RetriageAlert


coordinator_bp = Blueprint('coordinator', __name__, url_prefix='/api')

# coordinator_review.py



@coordinator_bp.route(
    '/assessments/<int:assessment_id>/explain',
    methods=['GET']
)
def explain_assessment(assessment_id):
    """
    Generate a natural-language explanation of an existing
    triage assessment using Gemini. Does NOT create a new
    assessment or change the ESI level in any way.
    """

    try:
        assessment = TriageAssessment.query.get(assessment_id)

        if not assessment:
            return jsonify({
                'error': 'Assessment not found'
            }), 404

        patient = Patient.query.get(assessment.patient_id)

        if not patient:
            return jsonify({
                'error': 'Patient not found'
            }), 404

        patient_payload = {
            'age': patient.age,
            'chief_complaint': patient.chief_complaint,
            'spo2': patient.spo2,
            'bp_systolic': patient.bp_systolic,
            'bp_diastolic': patient.bp_diastolic,
            'heart_rate': patient.heart_rate,
            'temperature': patient.temperature,
            'pain': patient.pain,
            'respiratory_rate': patient.respiratory_rate,
            'responsiveness': patient.responsiveness,
            'breathing': patient.breathing,
            'distress_level': patient.distress_level,
        }

        assessment_payload = {
            'esi_level': assessment.ai_esi_level,
            'confidence': float(assessment.ai_confidence)
                if assessment.ai_confidence is not None
                else None,
            'confidence_band': assessment.confidence_band,
            'reasoning': json.loads(assessment.ai_reasoning or '[]'),
            'auto_escalate_for_review':
                assessment.auto_escalate_for_review,
        }


        return jsonify({
            'assessment_id': assessment.id,
        }), 200

    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

@coordinator_bp.route(
    '/in-care',
    methods=['GET']
)
def get_in_care_patients():

    try:
        patients = (
            Patient.query
            .filter(
                Patient.status == 'in_care'
            )
            .order_by(
                Patient.arrival_time.asc()
            )
            .all()
        )

        result = []

        for patient in patients:

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

            decision = None

            if assessment:
                decision = (
                    CoordinatorDecision.query
                    .filter_by(
                        assessment_id=assessment.id
                    )
                    .first()
                )

            result.append({
                'patient_id': patient.id,
                'patient_uuid': patient.patient_id,
                'age': patient.age,
                'chief_complaint': patient.chief_complaint,

                'esi_level': (
                    decision.coordinator_esi_level
                    if decision
                    else (
                        assessment.ai_esi_level
                        if assessment
                        else None
                    )
                ),

                'arrival_time': (
                    patient.arrival_time.isoformat()
                    if patient.arrival_time
                    else None
                ),

                'status': patient.status,
            })

        return jsonify({
            'success': True,
            'patients': result,
        }), 200

    except Exception as e:

        return jsonify({
            'error': str(e)
        }), 500


@coordinator_bp.route(
    '/patients/<int:patient_id>/move-to-care',
    methods=['POST']
)
    
@coordinator_bp.route('/waiting-queue', methods=['GET'])
def get_waiting_queue():
    """
    Get patients who have completed initial triage and
    have a coordinator-approved ESI.

    A patient remains in the waiting queue while a
    re-triage assessment is awaiting review.
    """

    try:
        patients = Patient.query.filter(
            Patient.triage_completion_time.isnot(None),
            Patient.status.notin_([
               "in_care",
               "completed",
            ]),
        ).order_by(
            Patient.arrival_time.asc()
        ).all()

        queue = []

        for patient in patients:

            # --------------------------------------------------
            # Find the latest assessment WITH a coordinator
            # decision.
            #
            # Do NOT use only the latest assessment because
            # a new re-triage assessment may be waiting for
            # coordinator review.
            # --------------------------------------------------

            assessments = (
                TriageAssessment.query
                .filter_by(
                    patient_id=patient.id
                )
                .order_by(
                    TriageAssessment.id.desc()
                )
                .all()
            )

            decided_assessment = None
            decision = None

            for assessment in assessments:

                candidate_decision = (
                    CoordinatorDecision.query
                    .filter_by(
                        assessment_id=assessment.id
                    )
                    .first()
                )

                if candidate_decision:
                    decided_assessment = assessment
                    decision = candidate_decision
                    break

            # No coordinator-approved assessment yet.
            if not decided_assessment or not decision:
                continue

            # --------------------------------------------------
            # IMPORTANT:
            #
            # The patient stays in the queue even if there is
            # a newer re-triage assessment waiting for review.
            # --------------------------------------------------

            wait_minutes = (
                datetime.utcnow()
                - patient.arrival_time
            ).total_seconds() / 60

            queue.append({
                'patient_id': patient.id,

                'patient_uuid': patient.patient_id,

                'age': patient.age,

                'chief_complaint': patient.chief_complaint,

                # Use the latest coordinator-approved ESI.
                'esi_level': decision.coordinator_esi_level,

                'arrival_time': (
                    patient.arrival_time.isoformat()
                    if patient.arrival_time
                    else None
                ),

                'wait_time_minutes': round(
                    wait_minutes,
                    1
                ),

                'triage_completion_time': (
                    patient.triage_completion_time.isoformat()
                    if patient.triage_completion_time
                    else None
                ),

                # This is the assessment whose decision is
                # currently controlling the waiting queue.
                'assessment_id': decided_assessment.id,

                'is_override': decision.is_override,

                # Useful for the frontend/debugging.
                'has_pending_retriage': any(
                    CoordinatorDecision.query.filter_by(
                        assessment_id=a.id
                    ).first() is None
                    for a in assessments
                    if a.id != decided_assessment.id
                ),
            })

        return jsonify({
            'success': True,
            'patients': queue
        }), 200

    except Exception as e:

        return jsonify({
            'error': str(e)
        }), 500
    
@coordinator_bp.route(
    '/assessments/patient/<int:patient_id>',
    methods=['GET']
)
def get_patient_assessment(patient_id):
    """
    Get the latest pending triage assessment for a patient.

    Used by the coordinator review UI.
    A pending assessment is one that does not yet
    have a coordinator decision.
    """

    try:
        assessments = (
            TriageAssessment.query
            .filter_by(patient_id=patient_id)
            .order_by(TriageAssessment.id.desc())
            .all()
        )

        if not assessments:
            return jsonify({
                'error': 'No triage assessment found'
            }), 404

        # --------------------------------------------------
        # Find the newest assessment that has NOT yet been
        # reviewed by the coordinator.
        # --------------------------------------------------

        pending_assessment = None

        for assessment in assessments:

            decision = (
                CoordinatorDecision.query
                .filter_by(
                    assessment_id=assessment.id
                )
                .first()
            )

            if not decision:
                pending_assessment = assessment
                break

        # --------------------------------------------------
        # If every assessment has already been decided,
        # there is nothing left to review.
        # --------------------------------------------------

        if not pending_assessment:
            return jsonify({
                'error': 'Decision already made for this assessment'
            }), 409

        assessment = pending_assessment

        return jsonify({
            'assessment_id': assessment.id,
            'patient_id': assessment.patient_id,
            'esi_level': assessment.ai_esi_level,
            'confidence': (
                float(assessment.ai_confidence)
                if assessment.ai_confidence is not None
                else None
            ),
            'confidence_band': assessment.confidence_band,
            'reasoning': json.loads(
                assessment.ai_reasoning or '[]'
            ),
            'auto_escalate_for_review':
                assessment.auto_escalate_for_review
        }), 200

    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500
@coordinator_bp.route(
    "/coordinator-decision",
    methods=["POST"],
)
def make_decision():

    try:
        data = request.get_json() or {}

        assessment_id = data.get("assessment_id")
        coordinator_esi = data.get(
            "coordinator_esi_level"
        )
        is_override = data.get(
            "is_override",
            False,
        )
        reason = data.get(
            "override_reason",
            "",
        )

        # --------------------------------------------------
        # Validate
        # --------------------------------------------------

        if not assessment_id or coordinator_esi is None:
            return jsonify({
                "error": "Missing required fields"
            }), 400

        coordinator_esi = int(coordinator_esi)

        if not 1 <= coordinator_esi <= 5:
            return jsonify({
                "error": "ESI level must be 1-5"
            }), 400

        # --------------------------------------------------
        # Get exact assessment
        # --------------------------------------------------

        assessment = (
            TriageAssessment.query
            .filter_by(
                id=assessment_id
            )
            .first()
        )

        if not assessment:
            return jsonify({
                "error": "Assessment not found"
            }), 404

        # --------------------------------------------------
        # Prevent duplicate decision
        # --------------------------------------------------

        existing_decision = (
            CoordinatorDecision.query
            .filter_by(
                assessment_id=assessment.id
            )
            .first()
        )

        if existing_decision:
            return jsonify({
                "error": (
                    "Decision already made for "
                    "this assessment"
                )
            }), 409

        # --------------------------------------------------
        # Get patient
        # --------------------------------------------------

        patient = Patient.query.get(
            assessment.patient_id
        )

        if not patient:
            return jsonify({
                "error": "Patient not found"
            }), 404

        # --------------------------------------------------
        # Create coordinator decision
        # --------------------------------------------------

        decision_time = datetime.utcnow()

        decision = CoordinatorDecision(
            assessment_id=assessment.id,

            coordinator_esi_level=coordinator_esi,

            override_reason=(
                reason
                if is_override
                else None
            ),

            is_override=is_override,

            decision_time=decision_time,
        )

        db.session.add(decision)
        db.session.flush()

        # --------------------------------------------------
        # Complete triggered re-triage alert, if one exists
        # --------------------------------------------------

        completed_alert = complete_retriage(
            patient_id=patient.id,
            new_esi_level=coordinator_esi,
            assessment_id=assessment.id,
        )

        # --------------------------------------------------
        # Audit log
        # --------------------------------------------------

        audit_log = AuditLog(
            patient_id=patient.id,

            event_type=(
                "override"
                if is_override
                else "confirmation"
            ),

            timestamp=decision_time,

            ai_esi=assessment.ai_esi_level,

            ai_confidence=assessment.ai_confidence,

            coordinator_esi=coordinator_esi,

            coordinator_reasoning=reason,

            is_override=is_override,
        )

        db.session.add(audit_log)

        # --------------------------------------------------
        # Mark initial triage as completed
        #
        # Do NOT reset this during re-triage.
        # --------------------------------------------------

        if not patient.triage_completion_time:
            patient.triage_completion_time = decision_time

        # --------------------------------------------------
        # Start NEW monitoring cycle
        #
        # This happens after EVERY coordinator decision.
        #
        # Initial triage:
        #     starts the first timer.
        #
        # Re-triage:
        #     starts a fresh timer after the old alert
        #     was completed.
        # --------------------------------------------------

        new_alert = create_retriage_monitoring(
            patient_id=patient.id,
            esi_level=coordinator_esi,
        )

        # --------------------------------------------------
        # Commit everything together
        # --------------------------------------------------

        db.session.commit()

        return jsonify({
            "success": True,

            "decision_id": decision.id,

            "assessment_id": assessment.id,

            "coordinator_esi": coordinator_esi,

            "is_override": is_override,

            "completed_alert_id": (
                completed_alert.id
                if completed_alert
                else None
            ),

            "new_retriage_alert_id": (
                new_alert.id
                if new_alert
                else None
            ),

            "recorded_at": (
                decision_time.isoformat()
            ),
        }), 201

    except Exception as e:

        db.session.rollback()

        return jsonify({
            "error": str(e)
        }), 500

@coordinator_bp.route(
    '/patients/<int:patient_id>/complete',
    methods=['POST']
)
def complete_patient(patient_id):

    try:
        patient = Patient.query.get(patient_id)

        if not patient:
            return jsonify({
                'error': 'Patient not found'
            }), 404

        if patient.status != 'in_care':
            return jsonify({
                'error': 'Patient is not currently in care'
            }), 409

        patient.status = 'completed'

        # Close any remaining active re-triage alerts
        RetriageAlert.query.filter_by(
            patient_id=patient.id,
            retriaged=False
        ).update({
            'retriaged': True,
            'retriage_time': datetime.utcnow()
        })

        # Record completion in audit trail
        audit_log = AuditLog(
            patient_id=patient.id,
            event_type='completed',
            timestamp=datetime.utcnow()
        )

        db.session.add(audit_log)

        db.session.commit()

        return jsonify({
            'success': True,
            'patient_id': patient.id,
            'patient_identifier': patient.patient_id,
            'status': patient.status
        }), 200

    except Exception as e:
        db.session.rollback()

        return jsonify({
            'error': str(e)
        }), 500

    
@coordinator_bp.route(
    '/patients/<int:patient_id>/take-to-care',
    methods=['POST']
)
def take_patient_to_care(patient_id):
    try:
        patient = Patient.query.get(patient_id)

        if not patient:
            return jsonify({
                'error': 'Patient not found'
            }), 404

        if patient.status == 'in_care':
            return jsonify({
                'error': 'Patient is already in care'
            }), 409

        if patient.status == 'completed':
            return jsonify({
                'error': 'Patient is already completed'
            }), 409

        patient.status = 'in_care'

        # Stop any active re-triage alerts.
        RetriageAlert.query.filter_by(
            patient_id=patient.id,
            retriaged=False
        ).update({
            'retriaged': True,
            'retriage_time': datetime.utcnow()
        })

        # Record the transition in the audit trail.
        audit_log = AuditLog(
            patient_id=patient.id,
            event_type='taken_to_care',
            timestamp=datetime.utcnow()
        )

        db.session.add(audit_log)
        db.session.commit()

        return jsonify({
            'success': True,
            'patient_id': patient.id,
            'patient_identifier': patient.patient_id,
            'status': patient.status
        }), 200

    except Exception as e:
        db.session.rollback()

        return jsonify({
            'error': str(e)
        }), 500