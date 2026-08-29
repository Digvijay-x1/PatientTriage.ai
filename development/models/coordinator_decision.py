from datetime import datetime
from db import db

class CoordinatorDecision(db.Model):
    """Coordinator's decision on AI recommendation"""
    __tablename__ = 'coordinator_decisions'
    
    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey('triage_assessments.id'), nullable=False)
    
    # Coordinator's decision
    coordinator_esi_level = db.Column(db.Integer, nullable=False)
    override_reason = db.Column(db.Text, nullable=True)
    is_override = db.Column(db.Boolean, default=False)
    
    # Decision metadata
    decision_time = db.Column(db.DateTime, default=datetime.utcnow)
    coordinator_id = db.Column(db.String(100), nullable=True)  # For audit trail
    
    def __repr__(self):
        return f'<CoordinatorDecision ESI:{self.coordinator_esi_level} Override:{self.is_override}>'