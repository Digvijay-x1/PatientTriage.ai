from datetime import datetime, timedelta
from db import db

class RetriageAlert(db.Model):
    """Tracks re-triage monitoring and alerts"""
    __tablename__ = 'retriage_alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    
    # ESI level at arrival
    esi_level = db.Column(db.Integer, nullable=False)
    
    # Time thresholds
    arrival_time = db.Column(db.DateTime, nullable=False)
    next_recheck_time = db.Column(db.DateTime, nullable=False)  # When to trigger alert
    
    # Alert type
    alert_type = db.Column(db.String(50), nullable=False)  # time-based, event-driven
    
    # Status
    alert_triggered = db.Column(db.Boolean, default=False)
    alert_time = db.Column(db.DateTime, nullable=True)
    
    # Resolution
    retriaged = db.Column(db.Boolean, default=False)
    retriage_time = db.Column(db.DateTime, nullable=True)
    new_esi_level = db.Column(db.Integer, nullable=True)  # After re-triage
    
    def should_trigger(self):
        """Check if alert should trigger (wait time exceeded)"""
        if self.alert_triggered:
            return False
        return datetime.utcnow() >= self.next_recheck_time
    
    def __repr__(self):
        return f'<RetriageAlert Patient:{self.patient_id} ESI:{self.esi_level}>'