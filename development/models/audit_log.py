# Audit trail model
from datetime import datetime
from db import db

class AuditLog(db.Model):
    """Immutable audit trail of every triage decision"""
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    
    # Timestamps (immutable)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Event type
    event_type = db.Column(db.String(50), nullable=False)  # assessment, override, retriage, alert
    
    # AI Recommendation
    ai_esi = db.Column(db.Integer, nullable=True)
    ai_confidence = db.Column(db.Float, nullable=True)
    ai_reasoning = db.Column(db.Text, nullable=True)
    
    # Coordinator Decision
    coordinator_esi = db.Column(db.Integer, nullable=True)
    coordinator_reasoning = db.Column(db.Text, nullable=True)
    is_override = db.Column(db.Boolean, default=False)
    
    # Re-triage event (if applicable)
    retriage_reason = db.Column(db.String(200), nullable=True)  # time-based, event-driven, manual
    
    # Outcome (filled in later)
    actual_diagnosis = db.Column(db.String(200), nullable=True)
    ground_truth_esi = db.Column(db.Integer, nullable=True)
    
    def __repr__(self):
        return f'<AuditLog Patient:{self.patient_id} {self.event_type} at {self.timestamp}>'