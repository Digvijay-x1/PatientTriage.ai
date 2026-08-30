# POST /api/triage (run assessment)
from flask import Blueprint, request, jsonify
from datetime import datetime
import json
import traceback

from models.patient import Patient
from models.triage_assessment import TriageAssessment
from models.audit_log import AuditLog
from models.retriage_alert import RetriageAlert
from services.triage_service import run_triage_assessment
from services.retriage_service import create_retriage_monitoring
from db import db

triage_bp = Blueprint('triage', __name__, url_prefix='/api')

@triage_bp.route('/triage', methods=['POST'])
def assess_triage():
    """
    Run AI triage assessment on patient
    
    Request JSON:
    {
        "patient_id": 1  # Database ID
    }
    
    Response:
    {
        "esi_level": 2,
        "confidence": 0.87,
        "confidence_band": "high",
        "reasoning": [...],
        "auto_escalate_for_review": false,
        "assessment_id": 123
    }
    """
    
    try:
        data = request.get_json()
        patient_id = data.get('patient_id')
        
        if not patient_id:
            return jsonify({'error': 'patient_id required'}), 400
        
        # Fetch patient
        patient = Patient.query.get(patient_id)
        if not patient:
            return jsonify({'error': 'Patient not found'}), 404
        
        # Run Kavya's ML model. The service wrapper converts the DB Patient
        # record into Kavya's expected patient_dict schema.
        assessment_result = run_triage_assessment(patient)

        ai_confidence = assessment_result.get('confidence')

        if ai_confidence is None:
            ai_confidence = 0.0

        assessment = TriageAssessment(
            patient_id=patient.id,
            ai_esi_level=assessment_result['esi_level'],
            ai_confidence=ai_confidence,
            confidence_band=assessment_result['confidence_band'],
            ai_reasoning=json.dumps(
                assessment_result['reasoning']
            ),
            auto_escalate_for_review=assessment_result[
                'auto_escalate_for_coordinator_review'
            ],
            vital_details=json.dumps(
                assessment_result.get('vital_details', {})
            )
        )
        
        db.session.add(assessment)
        db.session.flush()  # Get assessment ID
        
        # Create audit log entry
        audit_log = AuditLog(
            patient_id=patient.id,
            event_type='assessment',
            timestamp=datetime.utcnow(),
            ai_esi=assessment_result['esi_level'],
            ai_confidence=ai_confidence,
            ai_reasoning=json.dumps(
                assessment_result['reasoning']
            )
        )
        
        db.session.add(audit_log)
        
        # Set up re-triage monitoring for this patient
        create_retriage_monitoring(patient.id, assessment_result['esi_level'])
        
        # Mark triage completion
        patient.triage_completion_time = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'assessment_id': assessment.id,
            'esi_level': assessment.ai_esi_level,
            'confidence': float(assessment.ai_confidence),
            'confidence_band': assessment.confidence_band,
            'reasoning': json.loads(assessment.ai_reasoning),
            'auto_escalate_for_review': assessment.auto_escalate_for_review
        }), 200
        
    except Exception as e:
        db.session.rollback()

        print("\n========== TRIAGE ERROR ==========")
        traceback.print_exc()
        print("==================================\n")

        return jsonify({
        "error": str(e)
        }), 500