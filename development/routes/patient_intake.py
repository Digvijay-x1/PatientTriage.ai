from flask import Blueprint, request, jsonify
from datetime import datetime
from models.patient import Patient
from db import db
from services.triage_service import run_triage_assessment
from models.triage_assessment import TriageAssessment
import json
from models.audit_log import AuditLog

intake_bp = Blueprint('intake', __name__, url_prefix='/api')


@intake_bp.route('/patients', methods=['POST'])
def register_patient():
    try:
        data = request.get_json()

        print("\n========== INCOMING PATIENT ==========")
        print("FULL DATA:", data)
        print("SEX:", repr(data.get("sex")))
        print("======================================\n")

        raw_sex = data.get('sex')

        if raw_sex is None:
            return jsonify({
                'error': 'Sex is required'
            }), 400

        sex = str(raw_sex).strip().lower()

        if sex not in ['male', 'female']:
            return jsonify({
                'error': 'Invalid sex value'
            }), 400

        required = [
            'patient_id',
            'age',
            'chief_complaint',
            'sex'
        ]

        if not all(field in data for field in required):
            return jsonify({
                'error': 'Missing required fields'
            }), 400

        patient = Patient(
            patient_id=data['patient_id'],
            age=data['age'],
            sex=data['sex'],
            chief_complaint=data['chief_complaint'],

            spo2=data.get('vitals', {}).get('spo2'),
            bp_systolic=data.get('vitals', {}).get('bp_systolic'),
            bp_diastolic=data.get('vitals', {}).get('bp_diastolic'),
            heart_rate=data.get('vitals', {}).get('heart_rate'),
            respiratory_rate=data.get('vitals', {}).get(
                'respiratory_rate'
            ),
            temperature=data.get('vitals', {}).get('temperature'),
            pain=data.get('vitals', {}).get('pain'),

            responsiveness=data.get(
                'observed', {}
            ).get('responsiveness'),

            breathing=data.get(
                'observed', {}
            ).get('breathing'),

            distress_level=data.get(
                'observed', {}
            ).get('distress_level'),

            has_prior_record=data.get(
                'has_prior_record',
                False
            ),

            history_cardiac=data.get(
                'history_cardiac',
                False
            ),

            history_respiratory=data.get(
                'history_respiratory',
                False
            ),

            history_diabetes=data.get(
                'history_diabetes',
                False
            ),

            history_renal=data.get(
                'history_renal',
                False
            ),

            history_hypertension=data.get(
                'history_hypertension',
                False
            ),

            clarifying_qa=str(
                data.get('clarifying_qa', {})
            ),

            status='waiting',
            arrival_time=datetime.utcnow(),
        )

        db.session.add(patient)
        db.session.flush()

        # ==========================================
        # INITIAL AI TRIAGE
        # ==========================================

        assessment_result = run_triage_assessment(
            patient,
            event_context={
                'event_type': 'initial-triage',
                'data': {},
            },
        )

        # ==========================================
        # NORMALIZE CONFIDENCE FOR DATABASE
        # ==========================================

        ai_confidence = assessment_result.get('confidence')

        if ai_confidence is None:
            ai_confidence = 0.0

        # ==========================================
        # SAVE TRIAGE ASSESSMENT
        # ==========================================

        assessment = TriageAssessment(
            patient_id=patient.id,

            ai_esi_level=assessment_result['esi_level'],

            ai_confidence=ai_confidence,

            confidence_band=assessment_result[
                'confidence_band'
            ],

            ai_reasoning=json.dumps(
                assessment_result.get(
                    'reasoning',
                    []
                )
            ),

            auto_escalate_for_review=assessment_result.get(
                'auto_escalate_for_coordinator_review',
                False
            ),

            vital_details=json.dumps(
                data.get('vitals', {})
            ),
        )

        db.session.add(assessment)
        db.session.flush()

        # ==========================================
        # AUDIT LOG
        # ==========================================

        audit_log = AuditLog(
            patient_id=patient.id,

            event_type='initial_assessment',

            timestamp=datetime.utcnow(),

            ai_esi=assessment_result['esi_level'],

            ai_confidence=ai_confidence,

            ai_reasoning=json.dumps(
                assessment_result.get(
                    'reasoning',
                    []
                )
            ),
        )

        db.session.add(audit_log)

        # ==========================================
        # COMMIT
        # ==========================================

        db.session.commit()

        return jsonify({
            'success': True,
            'patient_id': patient.id,
            'patient_uuid': patient.patient_id,
            'assessment_id': assessment.id,
            'esi_level': assessment_result['esi_level'],
        }), 201

    except Exception as e:
        db.session.rollback()

        return jsonify({
            'error': str(e)
        }), 500