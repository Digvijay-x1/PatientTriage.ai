# Patient data model
from datetime import datetime
from db import db

class Patient(db.Model):
    """Patient record (arrival data)"""
    __tablename__ = 'patients'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.String(50), unique=True, nullable=False)
    
    # Demographics
    age = db.Column(db.Integer, nullable=False)
    chief_complaint = db.Column(db.String(500), nullable=False)
    sex = db.Column(db.String(20),nullable=False,)
    
    # Vitals (captured at arrival)
    spo2 = db.Column(db.Float, nullable=True)
    bp_systolic = db.Column(db.Float, nullable=True)
    bp_diastolic = db.Column(db.Float, nullable=True)
    heart_rate = db.Column(db.Float, nullable=True)
    temperature = db.Column(db.Float, nullable=True)
    respiratory_rate = db.Column(db.Float, nullable=True)
    pain = db.Column(db.Float, nullable=True)
    
    # Observable data
    responsiveness = db.Column(db.String(100), nullable=True)  # alert, confused, unresponsive
    breathing = db.Column(db.String(100), nullable=True)       # normal, fast, labored
    distress_level = db.Column(db.String(100), nullable=True)  # none, mild, moderate, severe
    
    # History
    has_prior_record = db.Column(db.Boolean, nullable=False, default=False)

    history_cardiac = db.Column(db.Boolean, nullable=False, default=False)
    history_respiratory = db.Column(db.Boolean, nullable=False, default=False)
    history_diabetes = db.Column(db.Boolean, nullable=False, default=False)
    history_renal = db.Column(db.Boolean, nullable=False, default=False)
    history_hypertension = db.Column(db.Boolean, nullable=False, default=False)
    
    # Clarifying questions/answers
    clarifying_qa = db.Column(db.Text, nullable=True)     # JSON string
    
    # Timestamps
    arrival_time = db.Column(db.DateTime, default=datetime.utcnow)
    triage_completion_time = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    assessments = db.relationship('TriageAssessment', backref='patient', lazy=True)
    audit_entries = db.relationship('AuditLog', backref='patient', lazy=True)
    status = db.Column(db.String(20), default='waiting', nullable=False)  # waiting, triaged, in_review, completed

    
    def __repr__(self):
        return f'<Patient {self.patient_id}>'